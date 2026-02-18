# Mock Patterns — Common Mocking Strategies

AI-facing reference. Apply patterns by matching test scenario to strategy. Each pattern includes the correct module, setup, and verification idiom.

## Module Selection

```text
TRIGGER: Need to replace a method on an existing package
USE: Test::MockModule

TRIGGER: Need a standalone fake object with no real class
USE: Test::MockObject

TRIGGER: Using Test2 suite (Test2::V0, Test2::Bundle::*)
USE: Test2::Tools::Mock

TRIGGER: Need to mock AUTOLOAD or UNIVERSAL methods
USE: Test::MockObject (handles these; Test::MockModule does not)

TRIGGER: Need mock to expire at scope exit automatically
USE: Test::MockModule (destructor restores original)
```

## Test::MockModule Patterns

### Pattern: Method Replacement

```perl
use Test::MockModule;

my $mock = Test::MockModule->new('MyApp::Database');
$mock->mock('connect', sub { return 'fake_handle' });

# Code under test calls MyApp::Database->connect normally
# but gets 'fake_handle'

# Restore single method
$mock->unmock('connect');

# Restore all — or let $mock go out of scope (RAII)
$mock->unmock_all;
```

### Pattern: Call Tracking

```perl
my $mock = Test::MockModule->new('MyApp::Mailer');
my @calls;

$mock->mock('send', sub {
    my ($self, %args) = @_;
    push @calls, \%args;
    return 1;
});

trigger_notification();

is(scalar @calls, 1, 'send called once');
is($calls[0]{to}, 'user@example.com', 'correct recipient');
```

### Pattern: Call Count Assertion

```perl
my $mock = Test::MockModule->new('MyApp::Cache');
my $hit_count = 0;

$mock->mock('get', sub { $hit_count++; return undef });

fetch_with_cache('key1');
fetch_with_cache('key2');

is($hit_count, 2, 'cache consulted for each fetch');
```

### Pattern: Argument-Dependent Return

```perl
$mock->mock('query', sub {
    my ($self, $sql, @bind) = @_;
    return [{ id => 1 }] if $sql =~ /users/;
    return [{ id => 2 }] if $sql =~ /orders/;
    return [];
});
```

### Pattern: Stateful Mock (Sequential Returns)

```perl
my @responses = (undef, undef, { id => 1 });  # fail twice, succeed third

$mock->mock('fetch', sub {
    my $r = shift @responses;
    die 'not found' unless defined $r;
    return $r;
});
```

### Pattern: Scope-Bounded Mock

```perl
subtest 'isolated mock scope' => sub {
    my $mock = Test::MockModule->new('MyApp::HTTP');
    $mock->mock('get', sub { return { status => 200, body => 'ok' } });

    my $result = MyApp::Client->new->call('/api/users');
    is($result->{status}, 200, 'mocked HTTP returns 200');
};
# $mock destroyed here; MyApp::HTTP->get restored to original
```

### Pattern: Constructor Mock

```perl
my $fake_obj = bless { injected => 1 }, 'MyApp::DB';
$mock->mock('new', sub { return $fake_obj });

my $db = MyApp::DB->new;
ok($db->{injected}, 'factory returns injected object');
```

### Pattern: Error Simulation

```perl
use Test::Exception;

$mock->mock('connect', sub { die 'Connection refused' });

throws_ok { MyApp::Service->new->connect }
    qr/Connection refused/,
    'service propagates connection error';
```

### Pattern: Intermittent Failure

```perl
my $attempt = 0;
$mock->mock('connect', sub {
    $attempt++;
    die 'timeout' if $attempt < 3;
    return 'connected';
});

dies_ok  { $obj->connect } 'attempt 1 fails';
dies_ok  { $obj->connect } 'attempt 2 fails';
lives_ok { $obj->connect } 'attempt 3 succeeds';
```

## Test::MockObject Patterns

Use when the dependency has no real class, or you need a generic double with no backing implementation.

### Pattern: Standalone Fake Object

```perl
use Test::MockObject;

my $mock_logger = Test::MockObject->new;
$mock_logger->mock('info',  sub { });
$mock_logger->mock('error', sub { push @logged_errors, $_[1] });

MyApp::Service->new(logger => $mock_logger)->run;

is(scalar @logged_errors, 0, 'no errors logged');
```

### Pattern: Fake with Type Identity

```perl
my $mock_db = Test::MockObject->new;
$mock_db->set_isa('MyApp::Database');  # isa() and ref() return class name
$mock_db->mock('query', sub { return [] });

isa_ok($mock_db, 'MyApp::Database');
```

### Pattern: Call Inspection

```perl
my $mock = Test::MockObject->new;
$mock->set_true('save');   # returns 1
$mock->set_false('exists');  # returns 0 (but defined)

$service->save_record($mock);

ok($mock->called('save'), 'save was invoked');
my ($name, $args) = $mock->next_call;
is($name, 'save', 'first call was save');
```

### Pattern: set_* Convenience Helpers

```perl
$mock->set_true('connect');          # returns 1
$mock->set_false('is_error');        # returns '' (false)
$mock->set_undef('optional_field');  # returns undef
$mock->set_always('version', '5.7'); # always returns '5.7'
$mock->set_list('items', 1, 2, 3);  # returns list in list context
$mock->set_series('pop', 'a', 'b', 'c');  # returns in sequence
```

### Pattern: AUTOLOAD Mock

```perl
# Test::MockObject intercepts any method call not explicitly mocked
$mock->set_true('any_method_name');

# Or catch-all: make every unknown call return a value
$mock->mock('AUTOLOAD', sub { return 'default' });
```

## Test2::Tools::Mock Patterns

Use within Test2 suite. Integrated with Test2 lifecycle — mocks clean up automatically with subtests.

### Pattern: Basic Mock (Test2)

```perl
use Test2::V0;
use Test2::Tools::Mock qw(mock);

my $control = mock 'MyApp::Database' => (
    override => [
        connect => sub { return 'mock_handle' },
        query   => sub { return [] },
    ],
);

my $db = MyApp::Database->new;
is($db->connect, 'mock_handle', 'mocked connect');

# Restore by calling $control->reset or letting it go out of scope
```

### Pattern: add vs override

```perl
# override: replaces existing method; dies if method does not exist
mock 'MyApp::DB' => (override => [query => sub { [] }]);

# add: adds new method; dies if method already exists
mock 'MyApp::DB' => (add => [extra_method => sub { 1 }]);

# set: adds or overrides (does not check existence)
mock 'MyApp::DB' => (set => [any_method => sub { 1 }]);
```

### Pattern: Mock Subtest Scope

```perl
subtest 'isolated' => sub {
    my $m = mock 'MyApp::Service' => (
        override => [process => sub { return { ok => 1 } }],
    );
    my $result = MyApp::Controller->handle;
    is($result->{ok}, 1, 'process mocked');
    # $m and all overrides cleaned up at subtest end
};
```

## Anti-Patterns

### Anti-Pattern: Forgetting to Restore

```perl
# WRONG — leaks mock into subsequent tests
my $mock = Test::MockModule->new('MyApp::Cache');
$mock->mock('get', sub { undef });
# no scope or unmock — subsequent tests may fail non-deterministically
```

```perl
# CORRECT — scope-bounded or explicit unmock
{
    my $mock = Test::MockModule->new('MyApp::Cache');
    $mock->mock('get', sub { undef });
    # ... test ...
}  # mock restored here
```

### Anti-Pattern: Mocking the Wrong Package

```perl
# WRONG — mocks base class, but code calls derived class
my $mock = Test::MockModule->new('MyApp::Base');
# If code calls MyApp::Derived->query and Derived has its own query, mock has no effect

# CORRECT — mock the exact package the code under test calls
my $mock = Test::MockModule->new('MyApp::Derived');
```

### Anti-Pattern: Verifying Calls via Side Effects When Direct Inspection Available

```perl
# LESS PRECISE — uses indirect state to detect call
my $called = 0;
$mock->mock('save', sub { $called++ });
# ... run code ...
ok($called, 'save called');

# MORE PRECISE (Test::MockObject) — use built-in call inspection
ok($mock_obj->called('save'), 'save was called');
my (undef, $args) = $mock_obj->next_call('save');
is_deeply($args, [$expected_arg], 'save called with correct args');
```

### Anti-Pattern: Global State in Mock Closures

```perl
# WRONG — shared $count leaks between subtests if not reset
my $count = 0;
$mock->mock('send', sub { $count++ });

subtest 'first' => sub { trigger(); is($count, 1) };
subtest 'second' => sub { trigger(); is($count, 1) };  # fails: $count is 2

# CORRECT — declare $count inside each subtest or reset explicitly
subtest 'first' => sub {
    my $count = 0;
    $mock->mock('send', sub { $count++ });
    trigger();
    is($count, 1);
};
```

## Decision Tree

```text
Need to test code in isolation from a dependency?
│
├─ Dependency is a real Perl package already loaded?
│   ├─ YES → Test::MockModule (replaces methods on existing namespace)
│   └─ NO  → Test::MockObject (creates standalone double)
│
├─ Using Test2::V0 or Test2::Bundle::* throughout?
│   └─ YES → Test2::Tools::Mock (integrates with Test2 lifecycle)
│
├─ Need to mock AUTOLOAD or UNIVERSAL?
│   └─ YES → Test::MockObject (only option that intercepts these)
│
└─ Need call count / argument history without manual tracking?
    └─ YES → Test::MockObject (called(), next_call() built-in)
```

## Related Reference

Working mock examples with runnable test files: [mock_test.t](./test-examples/mock_test.t)
