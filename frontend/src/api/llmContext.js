/**
 * llmContext.js
 * API utility functions for managing LLM context files, domain knowledge, and templates.
 *
 * Functions:
 *   - fetchContextFiles: Fetch all context files
 *   - uploadContextFile: Upload a new context file
 *   - deleteContextFile: Delete a context file by id
 *   - fetchDomainKnowledge: Fetch domain knowledge text
 *   - updateDomainKnowledge: Update domain knowledge text
 *   - fetchTemplates: Fetch available templates
 *   - applyTemplate: Apply a template to domain knowledge
 */

/**
 * Fetch all context files
 * @returns {Promise<Array>} List of context files
 */
export async function fetchContextFiles() {
  const res = await fetch('/api/llm-context/files');
  if (!res.ok) throw new Error('Failed to fetch context files');
  return await res.json();
}

/**
 * Upload a new context file
 * @param {Object} data - File data to upload
 * @returns {Promise<Object>} The new context file object
 */
export async function uploadContextFile(data) {
  const res = await fetch('/api/llm-context/files', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to upload context file');
  return await res.json();
}

/**
 * Delete a context file by id
 * @param {string|number} id - Context file id
 * @returns {Promise<Object>} The deleted context file object
 */
export async function deleteContextFile(id) {
  const res = await fetch(`/api/llm-context/files/${id}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete context file');
  return await res.json();
}

/**
 * Fetch domain knowledge text
 * @returns {Promise<string>} Domain knowledge text
 */
export async function fetchDomainKnowledge() {
  const res = await fetch('/api/llm-context/domain');
  if (!res.ok) throw new Error('Failed to fetch domain knowledge');
  return await res.text();
}

/**
 * Update domain knowledge text
 * @param {Object} data - Domain knowledge data
 * @returns {Promise<string>} Updated domain knowledge text
 */
export async function updateDomainKnowledge(data) {
  const res = await fetch('/api/llm-context/domain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update domain knowledge');
  return await res.text();
}

/**
 * Fetch available templates
 * @returns {Promise<Array>} List of templates
 */
export async function fetchTemplates() {
  const res = await fetch('/api/llm-context/templates');
  if (!res.ok) throw new Error('Failed to fetch templates');
  return await res.json();
}

/**
 * Apply a template to domain knowledge
 * @param {Object} data - Template data
 * @returns {Promise<string>} Resulting domain knowledge text
 */
export async function applyTemplate(data) {
  const res = await fetch('/api/llm-context/templates/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to apply template');
  return await res.text();
}
