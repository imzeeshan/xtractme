// Send to LLM functionality
(function() {
    'use strict';
    
    function initSendToLLM() {
        // Wait for django.jQuery to be available
        var $ = null;
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
            $ = django.jQuery;
        } else if (typeof jQuery !== 'undefined') {
            $ = jQuery;
        } else {
            setTimeout(initSendToLLM, 50);
            return;
        }
        
        $(document).ready(function() {
            console.log('Send to LLM script loaded');
            // Handle click on Send to LLM buttons
            $(document).on('click', '.send-to-llm-btn', function(e) {
                e.preventDefault();
                console.log('Send to LLM button clicked');
                var $button = $(this);
                var documentId = $button.data('document-id');
                console.log('Document ID:', documentId);
                
                if (!documentId) {
                    alert('Error: Document ID not found');
                    return;
                }
                
                // Fetch available prompts, schemas, and pages
                console.log('Fetching LLM options...');
                fetchLLMOptions(documentId, function(prompts, schemas, pages) {
                    console.log('LLM options fetched, showing modal');
                    showLLMModal(documentId, prompts, schemas, pages, $button);
                });
            });
        });
    }
    
    function fetchLLMOptions(documentId, callback) {
        var $ = django.jQuery || jQuery;
        
        // Fetch prompts, schemas, and pages info
        $.ajax({
            url: '/admin/core/document/' + documentId + '/llm-options/',
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                console.log('LLM Options Response:', response);
                if (response.success) {
                    var prompts = response.prompts || {};
                    var schemas = response.schemas || {};
                    var pages = response.pages || [];
                    console.log('Prompts:', prompts);
                    console.log('Schemas:', schemas);
                    console.log('Pages:', pages);
                    callback(prompts, schemas, pages);
                } else {
                    alert('Error loading options: ' + (response.error || 'Unknown error'));
                }
            },
            error: function(xhr) {
                console.error('Error fetching LLM options:', xhr);
                // No fallback - only show database prompts
                alert('Error loading prompts. Please ensure you have active prompts configured in the admin panel.');
                callback({}, {}, []);
            }
        });
    }
    
    function showLLMModal(documentId, prompts, schemas, pages, $button) {
        var $ = django.jQuery || jQuery;
        
        // Create modal HTML
        var modalHtml = '<div id="llm-modal" style="display: none; position: fixed; z-index: 10000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4);">' +
            '<div style="background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 600px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">' +
            '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px;">' +
            '<h2 style="margin: 0; font-size: 18px; font-weight: 600;">Send to LLM</h2>' +
            '<span class="close-llm-modal" style="color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer;">&times;</span>' +
            '</div>' +
            '<form id="llm-form">' +
            '<div style="margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px;">' +
            '<label for="prompt-select" style="display: block; margin-bottom: 10px; font-weight: 600; font-size: 14px; color: #333;">Select Prompt:</label>' +
            '<select id="prompt-select" name="prompt_type" style="width: 100%; padding: 10px; border: 2px solid #417690; border-radius: 4px; font-size: 14px; background-color: white; cursor: pointer;">' +
            '</select>' +
            '</div>' +
            '<div style="margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px;">' +
            '<label for="schema-select" style="display: block; margin-bottom: 10px; font-weight: 600; font-size: 14px; color: #333;">Select Schema (Optional):</label>' +
            '<select id="schema-select" name="schema_id" style="width: 100%; padding: 10px; border: 2px solid #417690; border-radius: 4px; font-size: 14px; background-color: white; cursor: pointer;">' +
            '<option value="">-- No Schema --</option>' +
            '</select>' +
            '<div style="margin-top: 8px; font-size: 12px; color: #666; font-style: italic;">If selected, the LLM will structure the response according to this schema.</div>' +
            '</div>' +
            '<div style="margin-bottom: 20px;">' +
            '<label style="display: block; margin-bottom: 8px; font-weight: 500;">Select Pages:</label>' +
            '<div id="pages-container" style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 10px;">' +
            '</div>' +
            '<div style="margin-top: 10px;">' +
            '<button type="button" id="select-all-pages" class="button" style="margin-right: 10px; padding: 5px 10px; font-size: 12px;">Select All</button>' +
            '<button type="button" id="deselect-all-pages" class="button" style="padding: 5px 10px; font-size: 12px;">Deselect All</button>' +
            '</div>' +
            '</div>' +
            '<div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; border-top: 1px solid #ddd; padding-top: 15px;">' +
            '<button type="button" class="close-llm-modal button" style="padding: 8px 16px;">Cancel</button>' +
            '<button type="submit" class="button" style="padding: 8px 16px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer;">Send to LLM</button>' +
            '</div>' +
            '</form>' +
            '</div>' +
            '</div>';
        
        // Remove existing modal if any
        $('#llm-modal').remove();
        
        // Add modal to body
        $('body').append(modalHtml);
        var $modal = $('#llm-modal');
        
        // Populate prompts dropdown
        var $promptSelect = $('#prompt-select');
        console.log('Populating dropdown with prompts:', prompts);
        console.log('Number of prompts:', Object.keys(prompts).length);
        
        // Clear any existing options
        $promptSelect.empty();
        
        if (Object.keys(prompts).length === 0) {
            console.warn('No prompts available!');
            $promptSelect.append('<option value="">No prompts available</option>');
        } else {
            for (var promptName in prompts) {
                if (prompts.hasOwnProperty(promptName)) {
                    var displayName = prompts[promptName] || promptName;
                    $promptSelect.append('<option value="' + promptName + '">' + displayName + '</option>');
                    console.log('Added prompt option:', promptName, '->', displayName);
                }
            }
            // Set default to document_summary if available
            if (prompts['document_summary']) {
                $promptSelect.val('document_summary');
            } else {
                // Select first available prompt
                $promptSelect.prop('selectedIndex', 0);
            }
        }
        
        console.log('Dropdown populated. Current value:', $promptSelect.val());
        
        // Populate schemas dropdown
        var $schemaSelect = $('#schema-select');
        console.log('Populating dropdown with schemas:', schemas);
        console.log('Number of schemas:', Object.keys(schemas).length);
        
        // Clear existing options except the default "No Schema" option
        $schemaSelect.find('option:not(:first)').remove();
        
        if (Object.keys(schemas).length > 0) {
            for (var schemaId in schemas) {
                if (schemas.hasOwnProperty(schemaId)) {
                    var displayName = schemas[schemaId] || 'Schema ' + schemaId;
                    $schemaSelect.append('<option value="' + schemaId + '">' + displayName + '</option>');
                    console.log('Added schema option:', schemaId, '->', displayName);
                }
            }
        }
        
        console.log('Schema dropdown populated. Current value:', $schemaSelect.val());
        
        // Populate pages checkboxes
        var $pagesContainer = $('#pages-container');
        if (pages.length === 0) {
            $pagesContainer.html('<p style="color: #999; font-style: italic;">No pages available</p>');
        } else {
            pages.forEach(function(page) {
                var checkbox = '<label style="display: block; padding: 5px; cursor: pointer;">' +
                    '<input type="checkbox" name="selected_pages" value="' + page.id + '" checked style="margin-right: 8px;">' +
                    'Page ' + page.page_number + (page.text_preview ? ' - ' + page.text_preview.substring(0, 50) + '...' : '') +
                    '</label>';
                $pagesContainer.append(checkbox);
            });
        }
        
        // Select all pages button
        $('#select-all-pages').on('click', function() {
            $pagesContainer.find('input[type="checkbox"]').prop('checked', true);
        });
        
        // Deselect all pages button
        $('#deselect-all-pages').on('click', function() {
            $pagesContainer.find('input[type="checkbox"]').prop('checked', false);
        });
        
        // Close modal handlers
        $('.close-llm-modal').on('click', function() {
            $modal.remove();
        });
        
        // Form submit handler
        $('#llm-form').on('submit', function(e) {
            e.preventDefault();
            
            var promptType = $('#prompt-select').val();
            var schemaId = $('#schema-select').val();
            var selectedPages = [];
            $pagesContainer.find('input[type="checkbox"]:checked').each(function() {
                selectedPages.push($(this).val());
            });
            
            if (!promptType || promptType === '') {
                alert('Please select a prompt.');
                return;
            }
            
            if (selectedPages.length === 0) {
                alert('Please select at least one page.');
                return;
            }
            
            // Close modal
            $modal.remove();
            
            // Disable button and show loading
            $button.prop('disabled', true).text('Sending...');
            
            // Send to LLM
            sendToLLM(documentId, promptType, schemaId, selectedPages, $button);
        });
        
        // Show modal
        console.log('Showing modal with dropdown');
        $modal.fadeIn(200);
        
        // Verify dropdown is visible
        setTimeout(function() {
            var $promptSelect = $('#prompt-select');
            console.log('Modal visible. Dropdown exists:', $promptSelect.length > 0);
            console.log('Dropdown is visible:', $promptSelect.is(':visible'));
            console.log('Dropdown options count:', $promptSelect.find('option').length);
            if ($promptSelect.length > 0 && !$promptSelect.is(':visible')) {
                console.error('Dropdown exists but is not visible!');
            }
        }, 300);
    }
    
    function sendToLLM(documentId, promptType, schemaId, selectedPages, $button) {
        var $ = django.jQuery || jQuery;
        
        // Remove any existing response row for this document
        var responseDivId = 'llm-response-' + documentId;
        $('tr.llm-response-row[data-document-id="' + documentId + '"]').remove();
        $('#' + responseDivId).remove();
        
        // Build data object
        var requestData = {
            'prompt_type': promptType,
            'selected_pages': selectedPages
        };
        
        // Add schema_id only if one is selected
        if (schemaId && schemaId !== '') {
            requestData['schema_id'] = schemaId;
        }
        
        $.ajax({
            url: '/admin/core/document/' + documentId + '/send-to-llm/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            data: requestData,
            success: function(response) {
                $button.prop('disabled', false).text('Send to LLM');
                
                // Create response div below the button
                var $responseDiv = $('<div>', {
                    id: responseDivId,
                    class: 'llm-response-container',
                    style: 'margin-top: 10px; padding: 15px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; max-width: 100%; word-wrap: break-word;'
                });
                
                // Get the button's row for later use
                var $buttonRow = $button.closest('tr');
                
                if (response.success) {
                    var responseHtml = '<div style="position: relative;">' +
                        '<button type="button" class="close-llm-response" style="position: absolute; top: 5px; right: 5px; background: none; border: none; font-size: 20px; color: #999; cursor: pointer; padding: 0; width: 24px; height: 24px; line-height: 24px; text-align: center;" title="Close">&times;</button>' +
                        '<div style="margin-bottom: 10px; padding-right: 30px;">' +
                        '<strong style="color: #417690; font-size: 14px;">✓ Document analyzed successfully!</strong>' +
                        '</div>' +
                        '<div style="margin-bottom: 8px; font-size: 12px; color: #666;">' +
                        '<strong>Prompt used:</strong> ' + (response.prompt_name || promptType) + '<br>' +
                        (response.schema_name ? '<strong>Schema used:</strong> ' + response.schema_name + '<br>' : '') +
                        '<strong>Pages processed:</strong> ' + (response.pages_sent || selectedPages.length) +
                        '</div>' +
                        '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e0e0e0;">' +
                        '<strong style="font-size: 12px; color: #333;">LLM Response:</strong>' +
                        '<div style="margin-top: 8px; padding: 10px; background-color: white; border: 1px solid #e0e0e0; border-radius: 3px; max-height: 400px; overflow-y: auto; font-size: 13px; line-height: 1.6; white-space: pre-wrap;">' +
                        escapeHtml(response.response) +
                        '</div>' +
                        '<div style="margin-top: 8px; font-size: 11px; color: #999; font-style: italic;">' +
                        'LLM analysis has been saved to the document description field.' +
                        '</div>' +
                        '</div>' +
                        '</div>';
                    
                    $responseDiv.html(responseHtml);
                } else {
                    var errorHtml = '<div style="position: relative;">' +
                        '<button type="button" class="close-llm-response" style="position: absolute; top: 5px; right: 5px; background: none; border: none; font-size: 20px; color: #999; cursor: pointer; padding: 0; width: 24px; height: 24px; line-height: 24px; text-align: center;" title="Close">&times;</button>' +
                        '<div style="color: #d32f2f; font-weight: 600; margin-bottom: 8px; padding-right: 30px;">' +
                        '✗ Error processing document' +
                        '</div>' +
                        '<div style="color: #666; font-size: 13px;">' +
                        escapeHtml(response.error || 'Unknown error occurred') +
                        '</div>' +
                        '</div>';
                    
                    $responseDiv.html(errorHtml);
                }
                
                // Insert the response div in a new table row below the current row
                if ($buttonRow.length) {
                    // Get the number of columns in the table
                    var columnCount = $buttonRow.find('td, th').length;
                    
                    // Create a new row with a single cell spanning all columns
                    var $newRow = $('<tr>', {
                        class: 'llm-response-row',
                        'data-document-id': documentId
                    });
                    
                    var $newCell = $('<td>', {
                        colspan: columnCount,
                        style: 'padding: 10px;'
                    }).append($responseDiv);
                    
                    $newRow.append($newCell);
                    
                    // Insert the new row after the current row
                    $buttonRow.after($newRow);
                } else {
                    // Fallback: insert after the button
                    $button.after($responseDiv);
                }
            },
            error: function(xhr) {
                $button.prop('disabled', false).text('Send to LLM');
                
                var errorMsg = 'Error sending document to LLM';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 404) {
                    errorMsg = 'Endpoint not found. Please ensure the view is configured.';
                } else if (xhr.status === 500) {
                    errorMsg = 'Server error occurred. Please check the server logs.';
                } else {
                    errorMsg = 'Network error: ' + (xhr.statusText || 'Unknown error');
                }
                
                // Create error response div
                var $responseDiv = $('<div>', {
                    id: responseDivId,
                    class: 'llm-response-container',
                    style: 'margin-top: 10px; padding: 15px; background-color: #ffebee; border: 1px solid #ef5350; border-radius: 4px; max-width: 100%; word-wrap: break-word;'
                });
                
                var errorHtml = '<div style="position: relative;">' +
                    '<button type="button" class="close-llm-response" style="position: absolute; top: 5px; right: 5px; background: none; border: none; font-size: 20px; color: #999; cursor: pointer; padding: 0; width: 24px; height: 24px; line-height: 24px; text-align: center;" title="Close">&times;</button>' +
                    '<div style="color: #d32f2f; font-weight: 600; margin-bottom: 8px; padding-right: 30px;">' +
                    '✗ Error' +
                    '</div>' +
                    '<div style="color: #666; font-size: 13px;">' +
                    escapeHtml(errorMsg) +
                    '</div>' +
                    '</div>';
                
                $responseDiv.html(errorHtml);
                
                // Get the button's row for later use
                var $buttonRow = $button.closest('tr');
                
                // Insert the error div in a new table row below the current row
                if ($buttonRow.length) {
                    // Get the number of columns in the table
                    var columnCount = $buttonRow.find('td, th').length;
                    
                    // Create a new row with a single cell spanning all columns
                    var $newRow = $('<tr>', {
                        class: 'llm-response-row',
                        'data-document-id': documentId
                    });
                    
                    var $newCell = $('<td>', {
                        colspan: columnCount,
                        style: 'padding: 10px;'
                    }).append($responseDiv);
                    
                    $newRow.append($newCell);
                    
                    // Insert the new row after the current row
                    $buttonRow.after($newRow);
                    
                    // Add close button handler after row is inserted
                    $newRow.find('.close-llm-response').on('click', function() {
                        $newRow.remove();
                    });
                } else {
                    // Fallback: insert after the button
                    $button.after($responseDiv);
                    
                    // Add close button handler
                    $responseDiv.find('.close-llm-response').on('click', function() {
                        $responseDiv.remove();
                    });
                }
            }
        });
    }
    
    // Helper function to escape HTML
    function escapeHtml(text) {
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Start initialization
    initSendToLLM();
})();

