import apiClient from './client';

/**
 * Executes email text and embedded hyperlink analysis.
 * @param {{ subject?: string, message?: string, sender?: string }} payload
 */
export async function analyzeEmail(payload) {
  const response = await apiClient.post('/analyze/email', {
    subject: payload.subject || '',
    message: payload.message || '',
    sender: payload.sender || undefined,
  });
  return response.data;
}

/**
 * Executes standalone lexical URL phishing analysis.
 * @param {string} url
 */
export async function analyzeUrl(url) {
  const response = await apiClient.post('/analyze/url', {
    url: url.trim(),
  });
  return response.data;
}

/**
 * Uploads and analyzes a .eml RFC 822 email file.
 * @param {File} file
 */
export async function analyzeFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/analyze/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

/**
 * Uploads and analyzes a batch of .eml RFC 822 email files.
 * @param {File[]} files
 * @param {Function} [onUploadProgress]
 */
export async function analyzeFiles(files, onUploadProgress) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const response = await apiClient.post('/analyze/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });
  return response.data;
}
