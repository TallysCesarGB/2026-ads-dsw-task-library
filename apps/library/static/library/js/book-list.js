'use strict';

/**
 * Client-side filter for the book catalog.
 * Hides/shows <li> entries based on a case-insensitive match
 * against each book's title and author (read from data attributes).
 */
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('[data-book-search]');
    const catalog = document.querySelector('[data-catalog]');
    const noResults = document.querySelector('[data-no-results]');

    if (!searchInput || !catalog) {
        return;
    }

    const entries = Array.from(catalog.querySelectorAll('[data-entry]'));

    const normalize = (value) => value.trim().toLowerCase();

    const filterEntries = () => {
        const query = normalize(searchInput.value);
        let visibleCount = 0;

        entries.forEach((entry) => {
            const title = normalize(entry.dataset.title || '');
            const author = normalize(entry.dataset.author || '');
            const matches = query === '' || title.includes(query) || author.includes(query);

            entry.hidden = !matches;
            if (matches) {
                visibleCount += 1;
            }
        });

        if (noResults) {
            noResults.hidden = visibleCount !== 0;
        }
    };

    searchInput.addEventListener('input', filterEntries);
});