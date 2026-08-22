/**
 * Build the YAML frontmatter block that heads every per-page `.md` endpoint.
 *
 * Split out from `page-markdown.ts` because the hazard here is a pure string
 * problem and deserves to be tested as one: a title such as
 * `Evaluate RAG Accuracy: Q&A Evals` makes a bare `title: …` line invalid YAML
 * ("mapping values are not allowed here"), and the audience for these files is
 * precisely the machines that will try to parse them.
 *
 * `scripts/gitbook_to_starlight.py` already solved this the same way when it
 * wrote frontmatter into `src/content/docs`; this keeps the two consistent.
 */

/**
 * A YAML scalar that always round-trips.
 *
 * Every JSON string is a valid YAML double-quoted flow scalar, so
 * `JSON.stringify` is a complete quoter here — colons, `#`, quotes, leading
 * `[`/`{`/`*`/`&`, and newlines all come back out unchanged.
 *
 * @param {string} value
 * @returns {string}
 */
export function yamlScalar(value) {
	return JSON.stringify(String(value));
}

/**
 * `---` delimited frontmatter for one page. `description` is omitted entirely
 * when the page has none, rather than emitted empty.
 *
 * @param {{ title: string, description?: string }} data
 * @returns {string} the block, ending in a newline
 */
export function pageFrontmatter({ title, description }) {
	const lines = ['---', `title: ${yamlScalar(title)}`];
	if (description) lines.push(`description: ${yamlScalar(description)}`);
	lines.push('---', '');
	return lines.join('\n');
}
