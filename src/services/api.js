/**
 * API Service for Debtor Portal
 *
 * API Base URL is configured via environment variable VITE_API_BASE_URL
 * Set this in .env file at the project root
 */

// Get API base URL from environment variable, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Log API URL in development mode for debugging
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL);
}

// Helper function to convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      // Remove data:image/type;base64, prefix
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = error => reject(error);
  });
};

// Helper function for API calls
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  // Add auth token if available
  const token = localStorage.getItem('token');
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'API request failed');
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Helper function for status messages
const getStatusMessage = (statusData) => {
  const { status, processed_records, total_records, percentage } = statusData;
  
  switch (status) {
    case 'queued':
      return 'Upload queued, waiting for processor...';
    case 'processing':
      if (total_records > 0) {
        return `Processing: ${processed_records || 0} of ${total_records} records (${percentage || 0}%)`;
      }
      return 'Processing file...';
    case 'completed':
      return `Completed! Processed ${total_records} records.`;
    case 'failed':
      return 'Processing failed. Check errors.';
    default:
      return 'Processing...';
  }
};

// Admin API
export const adminApi = {
  login: async (username, password) => {
    return apiCall('/admin/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  },

  verifyOtp: async (username, otp) => {
    return apiCall('/admin/verify-otp/', {
      method: 'POST',
      body: JSON.stringify({ username, otp }),
    });
  },

  uploadExcel: async (file, onProgress) => {
    // Use presigned URL for large files (>10MB) to bypass API Gateway limit
    // Use regular async upload for smaller files
    const LARGE_FILE_THRESHOLD = 10 * 1024 * 1024; // 10MB (API Gateway limit)
    
    if (file.size > LARGE_FILE_THRESHOLD) {
      return adminApi.uploadExcelLarge(file, onProgress);
    }
    return adminApi.uploadExcelAsync(file, onProgress);
  },

  // For large files (>10MB) - uses presigned URL to bypass API Gateway limit
  uploadExcelLarge: async (file, onProgress) => {
    const token = localStorage.getItem('token');

    if (onProgress) {
      onProgress({ status: 'preparing', message: 'Preparing large file upload...', percentage: 0 });
    }

    // Step 1: Get presigned URL for direct S3 upload
    const presignedResponse = await fetch(`${API_BASE_URL}/admin/upload-presigned/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename: file.name,
        file_size: file.size,
      }),
    });

    const presignedData = await presignedResponse.json();
    if (!presignedResponse.ok) {
      throw new Error(presignedData.error || 'Failed to get upload URL');
    }

    const { job_id: jobId, presigned_url: presignedUrl } = presignedData;

    if (onProgress) {
      onProgress({ status: 'uploading', message: 'Uploading file to storage...', percentage: 10 });
    }

    // Step 2: Upload file directly to S3
    const uploadResponse = await fetch(presignedUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': 'application/octet-stream',
      },
    });

    if (!uploadResponse.ok) {
      throw new Error('Failed to upload file to storage');
    }

    if (onProgress) {
      onProgress({ status: 'queued', message: 'File uploaded, starting processing...', percentage: 20 });
    }

    // Step 3: Trigger processing
    const startResponse = await fetch(`${API_BASE_URL}/admin/upload-start-processing/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ job_id: jobId }),
    });

    const startData = await startResponse.json();
    if (!startResponse.ok) {
      throw new Error(startData.error || 'Failed to start processing');
    }

    // Step 4: Poll for completion (same as regular async)
    return adminApi.pollUploadStatus(jobId, onProgress);
  },

  uploadExcelAsync: async (file, onProgress) => {
    // Convert file to base64
    const fileData = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.readAsDataURL(file);
    });

    const token = localStorage.getItem('token');

    // Step 1: Upload file and trigger async processing
    const uploadResponse = await fetch(`${API_BASE_URL}/admin/upload-async/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename: file.name,
        file_data: fileData,
      }),
    });

    const uploadData = await uploadResponse.json();

    if (!uploadResponse.ok) {
      throw new Error(uploadData.error || 'Upload failed');
    }

    const jobId = uploadData.job_id;

    if (onProgress) {
      onProgress({ status: 'queued', message: 'Upload received, starting background processing...', percentage: 0 });
    }

    // Poll for completion
    return adminApi.pollUploadStatus(jobId, onProgress);
  },

  // Shared polling function - polls indefinitely until completed or failed
  pollUploadStatus: async (jobId, onProgress) => {
    const token = localStorage.getItem('token');
    const POLL_INTERVAL = 3000; // 3 seconds

    // Poll indefinitely until completed or failed
    while (true) {
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));

      try {
        const statusResponse = await fetch(`${API_BASE_URL}/admin/upload-status/${jobId}/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        const statusData = await statusResponse.json();

        if (onProgress) {
          onProgress({
            status: statusData.status,
            message: getStatusMessage(statusData),
            percentage: statusData.percentage || 0,
            processed: statusData.processed_records,
            total: statusData.total_records,
            inserted: statusData.inserted_count,
            updated: statusData.updated_count,
          });
        }

        if (statusData.status === 'completed') {
          return {
            success: true,
            message: `Successfully processed ${statusData.total_records} records`,
            job_id: jobId,
            inserted: statusData.inserted_count,
            updated: statusData.updated_count,
            errors: statusData.error_count,
          };
        }

        if (statusData.status === 'failed') {
          throw new Error(statusData.errors?.[0] || 'Processing failed');
        }
      } catch (pollError) {
        // If it's not a network error, re-throw
        if (pollError.message && !pollError.message.includes('fetch')) {
          throw pollError;
        }
        console.error('Poll error:', pollError);
        // Continue polling even if one request fails
      }
    }
  },

  getUploadStatus: async (jobId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/upload-status/${jobId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getAllDebtors: async (options = {}) => {
    const token = localStorage.getItem('token');
    const {
      page = 1,
      pageSize = 100,  // Increased default from 50 to 100
      search = '',
      sortBy = 'created_at',
      sortOrder = 'desc',
      debtType = '',
      uploadId = ''
    } = options;

    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    if (search) params.append('search', search);
    if (debtType) params.append('debt_type', debtType);
    if (uploadId) params.append('upload_id', uploadId);

    return apiCall(`/admin/debtors/?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  updateDebtor: async (accountNumber, updateData) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/debtor/${accountNumber}/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updateData),
    });
  },

  deleteDebtor: async (accountNumber) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/debtor/${accountNumber}/delete/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  bulkDeleteDebtors: async (accountNumbers) => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/debtors/bulk-delete/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ account_numbers: accountNumbers }),
    });
  },

  getNotifications: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/notifications/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  markNotificationRead: async (notificationId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/notifications/${notificationId}/read/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  markAllNotificationsRead: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/notifications/read-all/', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  uploadQrCode: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');

    try {
      // Try multipart upload first
      const response = await fetch(`${API_BASE_URL}/admin/qr-code/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        return data;
      }

      // If multipart fails, try base64 upload
      if (!response.ok && (response.status === 400 || data.error?.includes('No file uploaded'))) {
        console.log('Multipart upload failed, trying base64...');
        return await apiCall('/admin/qr-code/base64/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            filename: file.name,
            file_data: await fileToBase64(file)
          }),
        });
      }

      throw new Error(data.error || 'Upload failed');
    } catch (error) {
      console.error('QR Upload Error:', error);
      throw error;
    }
  },

  deleteQrCode: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/qr-code/delete/', {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  // Production QR Code Methods
  generateThaiPaymentQr: async (paymentData) => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/production-qr/thai-payment/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(paymentData),
    });
  },

  validateImageUpload: async (imageData) => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/production-qr/validate/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(imageData),
    });
  },

  getQrProcessingStatus: async () => {
    return apiCall('/admin/production-qr/status/', {
      method: 'GET',
    });
  },

  getUploadHistory: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/upload-history/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  downloadUploadFile: async (uploadId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/upload-history/${uploadId}/download/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  uploadDebtorImages: async (files) => {
    const formData = new FormData();
    for (const file of files) {
      formData.append('images', file);
    }

    const token = localStorage.getItem('token');

    // Create AbortController with 5 minute timeout for PDF processing
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

    try {
      const response = await fetch(`${API_BASE_URL}/admin/images/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Upload timeout - try smaller batch size for PDFs');
      }
      throw error;
    }
  },

  getDebtorImage: async (accountNumber) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/images/${accountNumber}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getDebtorImagesBatch: async (accountNumbers) => {
    const token = localStorage.getItem('adminToken');
    const accounts = accountNumbers.join(',');
    return apiCall(`/admin/images/batch/?accounts=${encodeURIComponent(accounts)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getDebtorImageUrl: (accountNumber) => {
    // Returns the direct URL to serve the image
    return `${API_BASE_URL}/admin/images/${accountNumber}/file/`;
  },

  deleteDebtorImage: async (accountNumber) => {
    const token = localStorage.getItem('adminToken');
    return apiCall(`/admin/images/${accountNumber}/delete/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  // Bulk QR Code Upload APIs (supports images, PDFs, ZIP files)
  // Now uses async processing with unlimited timeout (same as Excel upload)
  stageQrFiles: async (files, onProgress) => {
    try {
      console.log('stageQrFiles called with files:', files?.length || 0);
      // Use async upload for unlimited timeout
      const result = await adminApi.uploadQrAsync(files, onProgress);
      console.log('uploadQrAsync returned result:', result);
      console.log('Result type:', typeof result);
      console.log('Result keys:', result ? Object.keys(result) : 'null result');
      
      // Extra safety - ensure we're returning a plain object
      const safeResult = {
        success: Boolean(result?.success),
        uploaded: Number(result?.uploaded || 0),
        not_found: Number(result?.not_found || 0),
        skipped: Number(result?.skipped || 0),
        errors: Array.isArray(result?.errors) ? [...result.errors] : [],
        message: String(result?.message || 'Upload completed')
      };
      
      console.log('Returning safe result:', safeResult);
      console.log('Safe result errors:', safeResult.errors, 'length:', safeResult.errors.length);
      
      return safeResult;
    } catch (error) {
      console.error('stageQrFiles error:', error);
      console.error('Error stack:', error.stack);
      throw error;
    }
  },

  // Async QR Upload - supports ZIP, PDF, PNG, JPG with unlimited timeout
  uploadQrAsync: async (files, onProgress) => {
    const token = localStorage.getItem('token');
    
    if (!files || files.length === 0) {
      throw new Error('No files provided');
    }

    const LARGE_FILE_THRESHOLD = 1 * 1024 * 1024; // 1MB (force all files through large upload path)

    // Handle single file (ZIP, PDF, or single image)
    if (files.length === 1) {
      const file = files[0];
      
      try {
        if (file.size > LARGE_FILE_THRESHOLD) {
          console.log('Using large file upload for:', file.name);
          const result = await adminApi.uploadQrLarge(file, onProgress);
          console.log('Large file upload result:', result);
          return result;
        }

        if (onProgress) {
          onProgress({ status: 'preparing', message: 'Preparing QR upload...', percentage: 0 });
        }

        // Convert file to base64
        const base64Content = await fileToBase64(file);

        if (onProgress) {
          onProgress({ status: 'uploading', message: 'Uploading file...', percentage: 10 });
        }

        // Start async upload
        const response = await fetch(`${API_BASE_URL}/admin/qr/upload-async/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            filename: file.name,
            file_data: base64Content,
          }),
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || 'QR upload failed');
        }

        if (onProgress) {
          onProgress({ status: 'processing', message: 'Processing QR images...', percentage: 20 });
        }

        // Poll for completion
        const result = await adminApi.pollQrUploadStatus(data.job_id, onProgress);
        console.log('Poll result:', result);
        return result;
      } catch (singleFileError) {
        console.error('Single file upload error:', singleFileError);
        throw singleFileError;
      }
    }

    // Handle multiple individual files
    if (files.length > 1) {
      // Check if all files are images (PNG, JPG, etc.)
      const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'];
      const allAreImages = files.every(file => {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        return imageExtensions.includes(extension);
      });

      if (allAreImages) {
        // Create ZIP from multiple images and upload as single job
        if (onProgress) {
          onProgress({ status: 'preparing', message: 'Creating ZIP from images...', percentage: 5 });
        }

        // Dynamically import JSZip
        const JSZip = await import('jszip');
        const zip = new JSZip.default();

        // Add all files to ZIP
        for (const file of files) {
          zip.file(file.name, file);
        }

        if (onProgress) {
          onProgress({ status: 'preparing', message: 'Generating ZIP file...', percentage: 10 });
        }

        // Generate ZIP blob
        const zipBlob = await zip.generateAsync({
          type: 'blob',
          compression: 'DEFLATE',
          compressionOptions: { level: 6 }
        });

        // Create a new file object for the ZIP
        const zipFile = new File([zipBlob], `qr_images_${Date.now()}.zip`, {
          type: 'application/zip'
        });

        if (onProgress) {
          onProgress({ status: 'uploading', message: 'Uploading ZIP file...', percentage: 15 });
        }

        // Upload the ZIP as a single large file
        return await adminApi.uploadQrLarge(zipFile, onProgress);
      } else {
        // Multiple non-image files (likely ZIPs) - process one by one
        if (onProgress) {
          onProgress({ status: 'preparing', message: 'Processing multiple files...', percentage: 0 });
        }

        let totalUploaded = 0;
        let totalNotFound = 0;
        let allErrors = [];

        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const progressPercent = Math.round((i / files.length) * 80); // Reserve 20% for final summary
          
          if (onProgress) {
            onProgress({ 
              status: 'uploading', 
              message: `Processing file ${i + 1} of ${files.length}: ${file.name}...`, 
              percentage: progressPercent 
            });
          }

          try {
            // Upload each file individually using the large file method
            const result = await adminApi.uploadQrLarge(file, (fileProgress) => {
              // Update overall progress
              const overallPercent = progressPercent + Math.round((fileProgress.percentage || 0) / files.length);
              if (onProgress) {
                onProgress({
                  status: fileProgress.status,
                  message: `File ${i + 1}/${files.length}: ${fileProgress.message}`,
                  percentage: Math.min(overallPercent, 90)
                });
              }
            });

            totalUploaded += result.uploaded || 0;
            totalNotFound += result.not_found || 0;
            if (result.errors && Array.isArray(result.errors)) {
              allErrors = allErrors.concat(result.errors);
            }

          } catch (error) {
            allErrors.push(`${file.name}: ${error.message || 'Processing failed'}`);
          }
        }

        if (onProgress) {
          onProgress({ status: 'completed', message: 'All files processed', percentage: 100 });
        }

        return {
          success: true,
          uploaded: totalUploaded,
          not_found: totalNotFound,
          errors: allErrors,
          message: `Processed ${files.length} files. Uploaded: ${totalUploaded}, Not Found: ${totalNotFound}, Errors: ${allErrors.length}`
        };
      }
    }
  },

  // For large QR files (>10MB) - uses presigned URL
  uploadQrLarge: async (file, onProgress) => {
    const token = localStorage.getItem('token');

    if (onProgress) {
      onProgress({ status: 'preparing', message: 'Preparing large file upload...', percentage: 0 });
    }

    // Step 1: Get presigned URL
    const presignedResponse = await fetch(`${API_BASE_URL}/admin/qr/upload-presigned/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename: file.name,
        file_size: file.size,
        content_type: file.type || 'application/octet-stream',
      }),
    });

    const presignedData = await presignedResponse.json();

    if (!presignedResponse.ok) {
      throw new Error(presignedData.error || 'Failed to get upload URL');
    }

    const { job_id, upload_url } = presignedData;

    if (onProgress) {
      onProgress({ status: 'uploading', message: 'Uploading directly to S3...', percentage: 10 });
    }

    // Step 2: Upload file directly to S3
    const uploadResponse = await fetch(upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
      },
      body: file,
    });

    if (!uploadResponse.ok) {
      throw new Error('Failed to upload file to S3');
    }

    if (onProgress) {
      onProgress({ status: 'processing', message: 'Starting QR processing...', percentage: 20 });
    }

    // Step 3: Trigger processing
    const startResponse = await fetch(`${API_BASE_URL}/admin/qr/start-processing/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ job_id }),
    });

    const startData = await startResponse.json();

    if (!startResponse.ok) {
      throw new Error(startData.error || 'Failed to start processing');
    }

    // Step 4: Poll for completion
    return adminApi.pollQrUploadStatus(job_id, onProgress);
  },

  // Poll QR upload status - indefinite polling until complete
  pollQrUploadStatus: async (jobId, onProgress) => {
    const token = localStorage.getItem('token');
    const pollInterval = 3000; // 3 seconds

    // Indefinite polling - no timeout
    while (true) {
      try {
        const response = await fetch(`${API_BASE_URL}/admin/qr/upload-status/${jobId}/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        let statusData;
        try {
          const responseText = await response.text();
          console.log('Raw response:', responseText);
          statusData = JSON.parse(responseText);
          console.log('Parsed statusData:', statusData);
        } catch (jsonError) {
          console.error('Failed to parse JSON response:', jsonError);
          console.error('Response status:', response.status);
          console.error('Response headers:', Object.fromEntries(response.headers.entries()));
          throw new Error('Invalid response from server');
        }

        if (!response.ok) {
          // If unauthorized, the token might be expired
          if (response.status === 401) {
            if (onProgress) {
              onProgress({
                status: 'completed',
                message: 'Session expired during processing. Upload may have completed successfully. Please refresh the page to check.',
                percentage: 100,
              });
            }
            return {
              success: true,
              message: 'Session expired during processing. Upload may have completed successfully.',
            };
          }
          throw new Error(statusData.error || 'Failed to get status');
        }

        // Ensure statusData is an object
        if (typeof statusData !== 'object' || statusData === null) {
          console.error('Invalid statusData:', statusData);
          throw new Error('Invalid response format from server');
        }

        // Safely extract data with defaults
        const status = statusData.status || 'unknown';
        const total_images = statusData.total_images || 0;
        const processed_images = statusData.processed_images || 0;
        const percentage = statusData.percentage || 0;
        const uploaded_count = statusData.uploaded_count || 0;
        const not_found_count = statusData.not_found_count || 0;
        const skipped_count = statusData.skipped_count || 0;
        const error_count = statusData.error_count || 0;
        const errors = Array.isArray(statusData.errors) ? statusData.errors : [];

        // Generate status message
        let message = 'Processing...';
        switch (status) {
          case 'queued':
            message = 'Upload queued, waiting for processor...';
            break;
          case 'processing':
            if (total_images > 0) {
              message = `Processing: ${processed_images || 0} of ${total_images} images (${percentage || 0}%)`;
            } else {
              message = 'Extracting images from file...';
            }
            break;
          case 'completed':
            message = `Completed! Uploaded: ${uploaded_count}, Skipped: ${skipped_count}, Not Found: ${not_found_count}, Errors: ${error_count}`;
            break;
          case 'failed':
            message = 'Processing failed. Check errors.';
            break;
        }

        if (onProgress) {
          onProgress({
            status,
            message,
            percentage: percentage || 0,
            total_images,
            processed_images,
            uploaded_count,
            not_found_count,
            skipped_count,
            error_count,
            errors: Array.isArray(errors) ? errors : [],
          });
        }

        // Return when complete or failed
        if (status === 'completed') {
          console.log('Job completed, returning result with:', {
            uploaded_count,
            not_found_count,
            skipped_count,
            errors,
            errorsType: typeof errors,
            errorsIsArray: Array.isArray(errors)
          });
          
          // Create return object with extra safety
          const resultObject = {
            success: true,
            uploaded: Number(uploaded_count || 0),
            not_found: Number(not_found_count || 0),
            skipped: Number(skipped_count || 0),
            errors: Array.isArray(errors) ? [...errors] : [],
            message: String(message || 'Processing completed'),
          };
          
          console.log('About to return result object:', resultObject);
          console.log('Result object keys:', Object.keys(resultObject));
          console.log('Result object errors type:', typeof resultObject.errors, 'isArray:', Array.isArray(resultObject.errors));
          
          return resultObject;
        }

        if (status === 'failed') {
          let errorMessage = 'QR processing failed';
          if (errors) {
            if (Array.isArray(errors) && errors.length > 0) {
              errorMessage = errors[0];
            } else if (typeof errors === 'string') {
              errorMessage = errors;
            }
          }
          throw new Error(errorMessage);
        }

        // Continue polling
        await new Promise(resolve => setTimeout(resolve, pollInterval));

      } catch (pollError) {
        if (pollError.message && !pollError.message.includes('fetch')) {
          throw pollError;
        }
        console.error('Poll error:', pollError);
        // Continue polling even if one request fails
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }
  },

  getQrUploadStatus: async (jobId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/qr/upload-status/${jobId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  // Legacy stageQrFilesBase64 - now redirects to async upload
  stageQrFilesBase64: async (files, onProgress) => {
    return adminApi.uploadQrAsync(files, onProgress);
  },

  // Legacy PDF endpoints (backward compatibility)
  stagePdfFiles: async (files, jobId = null) => {
    return adminApi.stageQrFilesBase64(files);
  },

  stagePdfFilesBase64: async (files, jobId = null) => {
    return adminApi.stageQrFilesBase64(files);
  },

  finalizePdfStaging: async (jobId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/pdf/finalize/${jobId}/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  startPdfProcessing: async (jobId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/pdf/process/${jobId}/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getPdfProcessingStatus: async (jobId) => {
    const token = localStorage.getItem('token');
    return apiCall(`/admin/pdf/status/${jobId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getPdfJobs: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/pdf/jobs/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getAllPdfJobs: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/pdf/jobs/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getPaymentReceiptUrl: (filename) => {
    // Returns the direct URL to serve the payment receipt
    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/admin/receipts/${encodeURIComponent(filename)}/?token=${encodeURIComponent(token)}`;
  },

  getPaymentReceipt: async (filename) => {
    const token = localStorage.getItem('adminToken');
    const response = await fetch(`${API_BASE_URL}/admin/receipts/${encodeURIComponent(filename)}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Try to parse error as JSON, fallback to status text
      try {
        const data = await response.json();
        throw new Error(data.error || 'Failed to fetch receipt');
      } catch (e) {
        throw new Error(`Failed to fetch receipt: ${response.status} ${response.statusText}`);
      }
    }

    // Return the blob for download/display
    const blob = await response.blob();
    return blob;
  },

  changePassword: async (currentPassword, newPassword) => {
    const token = localStorage.getItem('token');
    return apiCall('/admin/change-password/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  },
};

// Public API for settings
export const settingsApi = {
  getQrCode: async () => {
    return apiCall('/settings/qr-code/', {
      method: 'GET',
    });
  },

  getSystemSettings: async () => {
    return apiCall('/settings/system/', {
      method: 'GET',
    });
  },
};

// QR Code API for debtors
export const qrApi = {
  // Get global LINE QR code for contact support (same for all users)
  getGlobalLineQr: async () => {
    return apiCall('/settings/qr-code/', {
      method: 'GET',
    });
  },

  // Get account-specific QR (payment QR or uploaded account image)
  getAccountQr: async (accountNumber) => {
    return apiCall(`/qr/account/${accountNumber}/`, {
      method: 'GET',
    });
  },

  // Get QR by National ID (finds account and returns specific QR)
  getQrByNationalId: async (nationalId) => {
    return apiCall(`/qr/national-id/${nationalId}/`, {
      method: 'GET',
    });
  },

  // Get legacy debtor-specific image/QR if available
  getDebtorImage: async (accountNumber) => {
    return apiCall(`/debtor/image/${accountNumber}/`, {
      method: 'GET',
    });
  },

  // Generate payment QR for specific debtor account (admin function)
  generatePaymentQr: async (accountNumber, nationalId = null) => {
    try {
      // First, get debtor account details
      const accountResponse = await debtorApi.getDebtorAccount(accountNumber);
      if (!accountResponse.success) {
        throw new Error('Account not found');
      }

      const account = accountResponse.account;
      
      // Generate QR with account information
      const qrData = {
        account_number: accountNumber,
        debtor_name: account.name,
        outstanding_balance: account.outstanding_balance,
        case_id: account.case_id,
        contact_info: 'hello@poweramc.co',
        national_id: nationalId || account.national_id
      };

      return apiCall('/admin/production-qr/thai-payment/', {
        method: 'POST',
        body: JSON.stringify(qrData),
      });
    } catch (error) {
      console.error('Error generating payment QR:', error);
      throw error;
    }
  },

  // Check QR processing capabilities
  getQrCapabilities: async () => {
    return apiCall('/admin/production-qr/status/', {
      method: 'GET',
    });
  }
};

// Super Admin API
export const superAdminApi = {
  getSystemSettings: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/superadmin/settings/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  updateSystemSettings: async (settings) => {
    const token = localStorage.getItem('token');
    return apiCall('/superadmin/settings/update/', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(settings),
    });
  },

  getAllAdmins: async () => {
    const token = localStorage.getItem('token');
    return apiCall('/superadmin/admins/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  resetAdminPassword: async (username, newPassword) => {
    const token = localStorage.getItem('token');
    return apiCall(`/superadmin/admins/${username}/reset-password/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ new_password: newPassword }),
    });
  },
};

// Debtor API
export const debtorApi = {
  login: async (loginValue, language = 'en', loginMethod = 'national_id') => {
    return apiCall('/debtor/login/', {
      method: 'POST',
      body: JSON.stringify({
        login_method: loginMethod,
        login_value: loginValue,
        national_id: loginValue, // For backward compatibility
        language: language
      }),
    });
  },

  verifyOtp: async (nationalId, otp) => {
    return apiCall('/debtor/verify-otp/', {
      method: 'POST',
      body: JSON.stringify({ national_id: nationalId, otp }),
    });
  },

  getAllAccounts: async () => {
    const token = localStorage.getItem('debtorToken');
    return apiCall('/debtor/accounts/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  getAccount: async (accountNumber) => {
    const token = localStorage.getItem('debtorToken');
    return apiCall(`/debtor/account/${accountNumber}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  updateContact: async (accountNumber, phone, email) => {
    const token = localStorage.getItem('debtorToken');
    return apiCall(`/debtor/account/${accountNumber}/contact/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ phone, email }),
    });
  },

  sendPaymentInterest: async (accountNumber, paymentType, paymentAmount, transactionNumber, receiptFile = null, language = 'en') => {
    const token = localStorage.getItem('debtorToken');

    // If there's a receipt file, use FormData
    if (receiptFile) {
      const formData = new FormData();
      formData.append('account_number', accountNumber);
      formData.append('payment_type', paymentType);
      formData.append('payment_amount', paymentAmount);
      formData.append('transaction_number', transactionNumber);
      formData.append('receipt', receiptFile);
      formData.append('language', language);

      const response = await fetch(`${API_BASE_URL}/debtor/payment-interest/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Payment submission failed');
      }
      return data;
    }

    // Otherwise use JSON
    return apiCall('/debtor/payment-interest/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        account_number: accountNumber,
        payment_type: paymentType,
        payment_amount: paymentAmount,
        installment_plan: transactionNumber,
        language: language,
      }),
    });
  },

  sendNotReadyToPay: async (accountNumber, reason, notes, language = 'en', preferredDate = '', preferredTime = '', preferredContactMethod = '', preferredContactValue = '', instalmentPlan = '') => {
    const token = localStorage.getItem('debtorToken');
    return apiCall('/debtor/not-ready-to-pay/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        account_number: accountNumber,
        reason: reason,
        notes: notes,
        language: language,
        preferred_contact_date: preferredDate,
        preferred_contact_time: preferredTime,
        preferred_contact_method: preferredContactMethod,
        preferred_contact_value: preferredContactValue,
        instalment_plan: instalmentPlan,
      }),
    });
  },

  savePdpaConsent: async () => {
    const token = localStorage.getItem('debtorToken');
    return apiCall('/debtor/pdpa-consent/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    });
  },

  savePaymentConsent: async () => {
    const token = localStorage.getItem('debtorToken');
    return apiCall('/debtor/payment-consent/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    });
  },
};

// Health check
export const healthCheck = async () => {
  return apiCall('/health/');
};

export default {
  adminApi,
  debtorApi,
  settingsApi,
  superAdminApi,
  healthCheck,
};
