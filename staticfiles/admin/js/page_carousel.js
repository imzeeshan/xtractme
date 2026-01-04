// Wait for django.jQuery to be available
(function() {
    'use strict';
    
    function initCarouselWhenReady() {
        // Check if django.jQuery is available
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
            var $ = django.jQuery;
            initPagePreviewCarousel($);
            setupEventHandlers($);
        } else if (typeof jQuery !== 'undefined') {
            // Fallback to global jQuery if available
            var $ = jQuery;
            initPagePreviewCarousel($);
            setupEventHandlers($);
        } else {
            // Wait a bit more for jQuery to load
            setTimeout(initCarouselWhenReady, 50);
        }
    }
    
    function setupEventHandlers($) {
        // Initialize carousel when document is ready
        $(document).ready(function() {
            initPagePreviewCarousel($);
        });
        
        // Re-initialize when inlines are added/removed
        $(document).on('formset:added formset:removed', function() {
            // Remove existing carousel and reinitialize
            $('.page-preview-carousel-container').remove();
            setTimeout(function() {
                initPagePreviewCarousel($);
            }, 100); // Small delay to ensure DOM is updated
        });
    }
    
    function initPagePreviewCarousel($) {
        // Find all inline groups with page previews
        var inlineGroups = $('.inline-group');
        
        inlineGroups.each(function() {
            var $group = $(this);
            var $previewItems = $group.find('.page-preview-carousel-item');
            
            // Skip if no preview items found or carousel already initialized
            if ($previewItems.length === 0) {
                return;
            }
            
            // Check if carousel already initialized for this group
            if ($group.closest('.inline-group').find('.page-preview-carousel-container').length > 0) {
                return; // Already initialized
            }
            
            // Get all preview items sorted by page number
            var items = [];
            $previewItems.each(function() {
                var $item = $(this);
                var pageNum = parseInt($item.data('page-number')) || 0;
                items.push({
                    element: this,
                    pageNumber: pageNum,
                    $element: $item
                });
            });
            
            // Sort by page number
            items.sort(function(a, b) {
                return a.pageNumber - b.pageNumber;
            });
            
            if (items.length === 0) {
                return;
            }
            
            // Store original parent for each item (for later restoration if needed)
            items.forEach(function(item) {
                item.$element.data('original-parent', item.$element.parent());
            });
            
            // Create carousel container
            var $carouselContainer = $('<div>', {
                'class': 'page-preview-carousel-container'
            });
            
            // Create controls
            var $controls = $('<div>', {
                'class': 'page-preview-carousel-controls'
            });
            
            var $nav = $('<div>', {
                'class': 'page-preview-carousel-nav'
            });
            
            var $prevBtn = $('<button>', {
                'class': 'page-preview-carousel-btn',
                text: '← Previous',
                type: 'button'
            });
            
            var $nextBtn = $('<button>', {
                'class': 'page-preview-carousel-btn',
                text: 'Next →',
                type: 'button'
            });
            
            var $indicator = $('<div>', {
                'class': 'page-preview-carousel-indicator',
                text: 'Page ' + items[0].pageNumber + ' of ' + items.length
            });
            
            $nav.append($prevBtn, $indicator, $nextBtn);
            $controls.append($nav);
            $carouselContainer.append($controls);
            
            // Create items container
            var $itemsContainer = $('<div>', {
                'class': 'page-preview-carousel-items'
            });
            
            // Move preview items to carousel (don't clone, move them)
            items.forEach(function(item, index) {
                var $item = item.$element.detach(); // Remove from original location
                $item.show(); // Make sure it's visible
                if (index > 0) {
                    $item.hide(); // Hide all except first
                }
                $itemsContainer.append($item);
            });
            
            $carouselContainer.append($itemsContainer);
            
            // Insert carousel before the inline group heading
            var $heading = $group.find('h2, .inline-heading').first();
            if ($heading.length) {
                $carouselContainer.insertAfter($heading);
            } else {
                $group.prepend($carouselContainer);
            }
            
            // Carousel state
            var currentIndex = 0;
            var $carouselItems = $itemsContainer.find('.page-preview-carousel-item');
            
            function updateCarousel() {
                // Hide all items
                $carouselItems.hide();
                
                // Show current item
                if ($carouselItems.eq(currentIndex).length) {
                    $carouselItems.eq(currentIndex).show();
                }
                
                // Update buttons
                $prevBtn.prop('disabled', currentIndex === 0);
                $nextBtn.prop('disabled', currentIndex === items.length - 1);
                
                // Update indicator
                var currentPageNum = items[currentIndex].pageNumber;
                $indicator.text('Page ' + currentPageNum + ' of ' + items.length);
            }
            
            // Navigation handlers
            $prevBtn.on('click', function() {
                if (currentIndex > 0) {
                    currentIndex--;
                    updateCarousel();
                }
            });
            
            $nextBtn.on('click', function() {
                if (currentIndex < items.length - 1) {
                    currentIndex++;
                    updateCarousel();
                }
            });
            
            // Keyboard navigation
            $carouselContainer.on('keydown', function(e) {
                if (e.key === 'ArrowLeft' && currentIndex > 0) {
                    e.preventDefault();
                    currentIndex--;
                    updateCarousel();
                } else if (e.key === 'ArrowRight' && currentIndex < items.length - 1) {
                    e.preventDefault();
                    currentIndex++;
                    updateCarousel();
                }
            });
            
            // Make container focusable for keyboard navigation
            $carouselContainer.attr('tabindex', '0');
            
            // Initialize
            updateCarousel();
        });
    }
    
    // Start initialization
    initCarouselWhenReady();
})();

