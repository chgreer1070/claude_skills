#!/usr/bin/env node
/**
 * Stop hook — reminds to capture new ideas and close completed items.
 */

const output = {
  additionalContext: `<backlog-reminder>
New ideas or deferred work discovered this session? → /work-backlog-item to add and track.
Completed items? → /work-backlog-item close {title} to verify and close.
</backlog-reminder>`,
};

console.log(JSON.stringify(output));
