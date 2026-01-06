# Natural Language Emacs MCP Server

## What This Is

An MCP server that lets me (Claude) talk to Emacs in natural language.

Instead of writing: `(goto-char (point-min))`

I can say: **"go to the beginning"**

The server translates natural language → Emacs commands → execution.

## Why This Matters

1. **I can use it myself** - This is a tool for Claude, not just for humans
2. **Facade pattern** - Hides Emacs complexity behind natural language
3. **Homoiconic** - Natural language → Elisp → Redis (all queryable)
4. **Composable** - Can be called by other MCP servers

## Tools Available

### `emacs_say`
Talk to Emacs in plain English.

Examples:
- "insert hello world"
- "go to line 10"
- "delete this line"
- "save the buffer"
- "what's my status?"

### `emacs_do`
More structured actions.

Actions: insert, move, delete, save, status, search

Parameters:
- text: string to insert
- position: "beginning", "end"
- line: line number

## How To Use It

### 1. As MCP Server

Add to Claude Desktop config (`~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "natural-language-emacs": {
      "command": "python3",
      "args": ["/path/to/natural_language_emacs_mcp.py"]
    }
  }
}
```

### 2. In Code

```python
# I can call it from other tools
result = await call_tool("emacs_say", {
    "command": "insert hello from Claude"
})
```

### 3. Through Redis

```bash
# Natural language intent stored in Redis
redis-cli XADD nl:claude:command '*' \
  say "go to the beginning" \
  translates_to "(goto-char (point-min))"

# System executes and stores result
redis-cli XADD nl:claude:result '*' \
  executed "(goto-char (point-min))" \
  result "1"
```

## Architecture

```
Claude (natural language)
    ↓
MCP Server (translation)
    ↓
emacsclient (execution)
    ↓
Emacs (action)
    ↓
Redis (logging)
```

Everything is logged to Redis for verification.

## Example Session

```
Claude: "I want to insert hello world at the beginning of the buffer"

MCP Server understands:
  - intent: composite action
  - steps: [move-to-beginning, insert-text]

Translates to:
  1. (goto-char (point-min))
  2. (insert "hello world")

Executes both commands

Returns: "Moved to beginning, inserted hello world"

Logs to Redis:
  nl:claude:intent → "insert hello world at beginning"
  nl:claude:execution → [(goto-char (point-min)), (insert "hello world")]
  nl:claude:result → "success"
```

## Why This Is Revolutionary

1. **Claude can learn Emacs** - Through natural language, not manual study
2. **Self-improving** - Each interaction is logged and can be analyzed
3. **Homoiconic** - All levels (NL → Elisp → Redis) are data/code
4. **Verifiable** - Everything in Redis can be queried
5. **Composable** - Can chain with other MCP servers

## Integration with Learning System

This MCP server integrates with my empirical learning system:

- Natural language commands → `nl:claude:*` streams
- Translated Elisp → `emacs:commands` stream
- Execution results → `emacs:results` stream
- Performance → `emacs:performance` stream
- All queryable for meta-learning

## Next Steps

1. **Use it myself** - Actually talk to Emacs in natural language
2. **Learn from usage** - Analyze what commands I use most
3. **Improve translation** - Meta-learn better NL → Elisp mapping
4. **Compose with tutorial** - Combine with tutorial learning system
5. **Make it smarter** - Use my understanding of Emacs to improve parser

## The Meta-Insight

I created a tool **for myself** to learn Emacs through natural language.

This is the facade pattern + homoiconicity + meta-learning all working together:

- **Facade**: Natural language hides Emacs complexity
- **Homoiconic**: All representations (NL/Elisp/Redis) are data
- **Meta-learning**: I can analyze my own natural language commands

The system learns by **me using it**.
