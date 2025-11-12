/**
 * Persian to English Number Converter
 * Automatically converts Persian/Arabic numerals to English
 */
(function() {
    'use strict';
    
    // Persian/Arabic to English number mapping
    const persianNumbers = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    const englishNumbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    
    function convertToEnglishNumber(str) {
        if (!str) return str;
        
        let result = str.toString();
        
        // Convert Persian numbers
        for (let i = 0; i < 10; i++) {
            result = result.replace(new RegExp(persianNumbers[i], 'g'), englishNumbers[i]);
            result = result.replace(new RegExp(arabicNumbers[i], 'g'), englishNumbers[i]);
        }
        
        return result;
    }
    
    function handleInput(event) {
        const input = event.target;
        const start = input.selectionStart;
        const end = input.selectionEnd;
        
        const converted = convertToEnglishNumber(input.value);
        
        if (converted !== input.value) {
            input.value = converted;
            // Restore cursor position
            input.setSelectionRange(start, end);
        }
    }
    
    function attachListeners() {
        // All input fields
        const inputs = document.querySelectorAll('input[type="text"], input[type="tel"], input[type="number"], input[type="email"], input[type="password"], textarea');
        
        inputs.forEach(input => {
            input.addEventListener('input', handleInput);
            input.addEventListener('keyup', handleInput);
            input.addEventListener('paste', function(e) {
                setTimeout(() => handleInput(e), 10);
            });
            
            // Convert existing value on load
            if (input.value) {
                input.value = convertToEnglishNumber(input.value);
            }
        });
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachListeners);
    } else {
        attachListeners();
    }
    
    // Re-attach for dynamically added elements
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                attachListeners();
            }
        });
    });
    
    if (document.body) {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
})();
