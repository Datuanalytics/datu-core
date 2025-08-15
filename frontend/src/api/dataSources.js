/**
 * dataSources.js
 * API utility functions for managing data sources (files and databases).
 *
 * Functions:
 *   - uploadDataSourceFile: Upload CSV/Excel file as data source
 *   - addDatabaseSource: Add database connection as data source
 *   - fetchDataSources: Fetch all data sources
 *   - updateDataSource: Update a data source by id
 *   - deleteDataSource: Delete a data source by id
 */

/**
 * Upload CSV/Excel file as data source
 * @param {File} file - The file to upload
 * @returns {Promise<Object>} The new data source object
 */
export async function uploadDataSourceFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/data-sources/files', {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload data source file');
  return await res.json();
}

/**
 * Add database connection as data source
 * @param {Object} data - Database connection details
 * @returns {Promise<Object>} The new data source object
 */
export async function addDatabaseSource(data) {
  const res = await fetch('/api/data-sources/databases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to add database source');
  return await res.json();
}

/**
 * Fetch all data sources
 * @returns {Promise<Array>} List of data sources
 */
export async function fetchDataSources() {
  const res = await fetch('/api/data-sources');
  if (!res.ok) throw new Error('Failed to fetch data sources');
  return await res.json();
}

/**
 * Update a data source by id
 * @param {string|number} id - Data source id
 * @param {Object} data - Data to update
 * @returns {Promise<Object>} The updated data source object
 */
export async function updateDataSource(id, data) {
  const res = await fetch(`/api/data-sources/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update data source');
  return await res.json();
}

/**
 * Delete a data source by id
 * @param {string|number} id - Data source id
 * @returns {Promise<Object>} The deleted data source object
 */
export async function deleteDataSource(id) {
  const res = await fetch(`/api/data-sources/${id}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete data source');
  return await res.json();
}
