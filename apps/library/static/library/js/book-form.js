'use strict';

/**
 * Searchable multi-select used for the "authors" and "category" fields.
 *
 * It enhances a regular <select multiple> (kept in the DOM and still the source
 * of truth for existing items). Names that don't exist yet are stored as hidden
 * inputs (`new_authors` / `new_categories`) and created by the server on save.
 * Without JavaScript the plain <select multiple> is shown instead.
 */
(() => {
    // Case- and accent-insensitive comparison ("jose" matches "José").
    const normalize = (value) =>
        value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
    const collapse = (value) => value.trim().replace(/\s+/g, ' ');

    function initCombo(root) {
        const select = root.querySelector('select');
        const box = root.querySelector('[data-combo-box]');
        const chipList = root.querySelector('[data-chips]');
        const input = root.querySelector('[data-combo-input]');
        const list = root.querySelector('[data-combo-list]');
        if (!select || !box || !chipList || !input || !list) {
            return;
        }

        const newName = root.dataset.newName;
        const addLabel = root.dataset.addLabel || 'item';
        const emptyText = root.dataset.empty || 'Nenhuma opção disponível.';
        const options = Array.from(select.options);
        const fieldLabel = root.parentElement.querySelector('label');

        let entries = [];
        let active = -1;

        // Swap the plain <select> for the enhanced control.
        select.hidden = true;
        box.hidden = false;
        if (fieldLabel) {
            fieldLabel.setAttribute('for', input.id);
        }

        const newInputs = () => Array.from(root.querySelectorAll('input[data-new]'));

        const addNew = (name) => {
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = newName;
            hidden.value = name;
            hidden.setAttribute('data-new', '');
            root.appendChild(hidden);
        };

        // ---- chips (selected values) ----

        const buildChip = (text, isNew, onRemove) => {
            const chip = document.createElement('li');
            chip.className = isNew ? 'chip is-new' : 'chip';

            const label = document.createElement('span');
            label.textContent = text;
            chip.appendChild(label);

            if (isNew) {
                const flag = document.createElement('em');
                flag.className = 'chip-flag';
                flag.textContent = 'novo';
                chip.appendChild(flag);
            }

            const remove = document.createElement('button');
            remove.type = 'button';
            remove.setAttribute('aria-label', `Remover ${text}`);
            remove.textContent = '\u00d7';
            remove.addEventListener('click', () => {
                onRemove();
                refresh();
                input.focus();
            });
            chip.appendChild(remove);

            return chip;
        };

        const renderChips = () => {
            chipList.replaceChildren();
            options
                .filter((option) => option.selected)
                .forEach((option) => {
                    chipList.appendChild(
                        buildChip(option.text, false, () => {
                            option.selected = false;
                        })
                    );
                });
            newInputs().forEach((hidden) => {
                chipList.appendChild(buildChip(hidden.value, true, () => hidden.remove()));
            });
        };

        // ---- suggestion list ----

        const buildEntries = () => {
            const query = normalize(input.value);

            const found = options
                .filter(
                    (option) =>
                        !option.selected &&
                        (query === '' || normalize(option.text).includes(query))
                )
                .sort(
                    (a, b) =>
                        Number(normalize(b.text).startsWith(query)) -
                        Number(normalize(a.text).startsWith(query))
                )
                .map((option) => ({ type: 'option', option, label: option.text }));

            const typed = collapse(input.value);
            if (typed) {
                const taken =
                    options.some((option) => normalize(option.text) === query) ||
                    newInputs().some((hidden) => normalize(hidden.value) === query);
                if (!taken) {
                    found.push({ type: 'new', label: typed });
                }
            }
            return found;
        };

        const setActive = (index) => {
            active = index;
            Array.from(list.querySelectorAll('[role="option"]')).forEach((item, i) => {
                const isActive = i === index;
                item.classList.toggle('is-active', isActive);
                item.setAttribute('aria-selected', String(isActive));
                if (isActive) {
                    input.setAttribute('aria-activedescendant', item.id);
                    if (item.scrollIntoView) {
                        item.scrollIntoView({ block: 'nearest' });
                    }
                }
            });
            if (index < 0) {
                input.removeAttribute('aria-activedescendant');
            }
        };

        const renderList = () => {
            entries = buildEntries();
            list.replaceChildren();

            if (entries.length === 0) {
                const empty = document.createElement('li');
                empty.className = 'combo-empty';
                empty.setAttribute('role', 'presentation');
                empty.textContent = input.value.trim() ? 'Nenhum resultado.' : emptyText;
                list.appendChild(empty);
            }

            entries.forEach((entry, i) => {
                const item = document.createElement('li');
                item.id = `${list.id}-opt-${i}`;
                item.setAttribute('role', 'option');
                item.className = entry.type === 'new' ? 'combo-option is-add' : 'combo-option';
                item.textContent =
                    entry.type === 'new'
                        ? `Adicionar ${addLabel} \u201c${entry.label}\u201d`
                        : entry.label;
                // mousedown (not click) keeps the focus on the text input.
                item.addEventListener('mousedown', (event) => {
                    event.preventDefault();
                    choose(entry);
                });
                item.addEventListener('mousemove', () => {
                    if (active !== i) {
                        setActive(i);
                    }
                });
                list.appendChild(item);
            });

            setActive(Math.min(active, entries.length - 1));
        };

        const open = () => {
            renderList();
            list.hidden = false;
            input.setAttribute('aria-expanded', 'true');
        };

        const close = () => {
            list.hidden = true;
            input.setAttribute('aria-expanded', 'false');
            active = -1;
            input.removeAttribute('aria-activedescendant');
        };

        const refresh = () => {
            renderChips();
            if (!list.hidden) {
                renderList();
            }
        };

        function choose(entry) {
            if (entry.type === 'option') {
                entry.option.selected = true;
            } else {
                addNew(entry.label);
            }
            input.value = '';
            active = -1;
            renderChips();
            renderList();
            input.focus();
        }

        const removeLast = () => {
            const added = newInputs();
            if (added.length) {
                added[added.length - 1].remove();
            } else {
                const selected = options.filter((option) => option.selected);
                if (!selected.length) {
                    return;
                }
                selected[selected.length - 1].selected = false;
            }
            refresh();
        };

        // ---- events ----

        input.addEventListener('input', () => {
            active = input.value.trim() ? 0 : -1;
            open();
        });

        input.addEventListener('focus', open);
        input.addEventListener('click', () => {
            if (list.hidden) {
                open();
            }
        });

        input.addEventListener('keydown', (event) => {
            switch (event.key) {
                case 'ArrowDown':
                    event.preventDefault();
                    if (list.hidden) {
                        open();
                    } else if (entries.length) {
                        setActive((active + 1) % entries.length);
                    }
                    break;
                case 'ArrowUp':
                    event.preventDefault();
                    if (list.hidden) {
                        open();
                    } else if (entries.length) {
                        setActive(active <= 0 ? entries.length - 1 : active - 1);
                    }
                    break;
                case 'Enter':
                    if (!list.hidden && entries[active]) {
                        event.preventDefault();
                        choose(entries[active]);
                    } else if (input.value.trim()) {
                        // Never submit the form while a name is half-typed.
                        event.preventDefault();
                    }
                    break;
                case 'Escape':
                    if (!list.hidden) {
                        event.preventDefault();
                        close();
                    }
                    break;
                case 'Backspace':
                    if (input.value === '') {
                        removeLast();
                    }
                    break;
                default:
                    break;
            }
        });

        // Clicking empty space inside the box focuses the text input.
        box.addEventListener('click', (event) => {
            if (event.target === box || event.target === chipList) {
                input.focus();
            }
        });

        // Close when focus leaves the whole control (Tab, click elsewhere).
        root.addEventListener('focusout', (event) => {
            if (!root.contains(event.relatedTarget)) {
                close();
            }
        });

        renderChips();
    }

    const init = () => document.querySelectorAll('[data-combo]').forEach(initCombo);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();