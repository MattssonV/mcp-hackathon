## MCP Tools

### `extract_competition_table`

Fetches competition results tables from the Swedish figure skating results pages (or any HTML page with a `<table>` element).

**Parameters**

- `url` (str): Page URL containing the table.
- `table_index` (int, default `0`): Which table to extract when multiple are present.
- `output_format` (str, default `"csv"`): Either `"csv"` or `"json"`.

**Example invocation**

```json
{
	"name": "extract_competition_table",
	"arguments": {
		"url": "https://skate.webbplatsen.net/23-24/70831/html/SEG004.htm",
		"table_index": 0,
		"output_format": "csv"
	}
}
```

The tool returns the table as a CSV string (or JSON if requested), ready for additional processing or visualization.
