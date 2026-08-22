export const qs = (selector, root = document) => root.querySelector(selector);
export const qsa = (selector, root = document) => root.querySelectorAll(selector);

export function syncSelectedOptionTitle(select) {
  const selectedOption = select.selectedOptions[0];
  select.title = select.value && selectedOption ? selectedOption.textContent.trim() : "";
}

export function appendDoseInput(cell, input, unitSymbol) {
  const wrapper = document.createElement("span");
  wrapper.className = "dose-input";
  const unit = document.createElement("span");
  unit.className = "dose-input-unit";
  unit.textContent = unitSymbol;
  wrapper.append(input, unit);
  cell.appendChild(wrapper);
}

export function createSearchableCombobox({
  id,
  options,
  value,
  onCommit,
  accessibleLabel,
  emptyLabel,
  noResultsLabel,
  placeholder,
}) {
  const root = document.createElement("div");
  const input = document.createElement("input");
  const listbox = document.createElement("div");
  const listboxId = `${id}-listbox`;
  const fertilizerNames = options.map(({ name }) => name);
  const selectedValue = value || "";
  let activeIndex = -1;
  let visibleNames = [];
  let dirty = false;

  root.className = "searchable-combobox";
  input.id = id;
  input.className = "searchable-combobox-input";
  input.type = "text";
  input.value = selectedValue;
  input.placeholder = placeholder;
  input.autocomplete = "off";
  input.spellcheck = false;
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-controls", listboxId);
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-label", accessibleLabel);

  listbox.id = listboxId;
  listbox.className = "searchable-combobox-listbox";
  listbox.setAttribute("role", "listbox");
  listbox.setAttribute("aria-label", accessibleLabel);

  function normalized(valueToNormalize) {
    return String(valueToNormalize || "").trim().toLowerCase();
  }

  function positionListbox() {
    if (!listbox.isConnected) return;
    const inputRect = input.getBoundingClientRect();
    const { clientWidth: viewportWidth, clientHeight: viewportHeight } = document.documentElement;
    if (inputRect.bottom < 8 || inputRect.top > viewportHeight - 8) {
      close();
      return;
    }
    const width = Math.min(Math.max(inputRect.width, 320), viewportWidth - 16);
    const spaceBelow = viewportHeight - inputRect.bottom - 12;
    const spaceAbove = inputRect.top - 12;
    const openAbove = spaceBelow < 180 && spaceAbove > spaceBelow;
    const availableHeight = Math.max(96, openAbove ? spaceAbove : spaceBelow);
    Object.assign(listbox.style, {
      width: `${width}px`,
      maxHeight: `${Math.min(320, availableHeight)}px`,
      left: `${Math.max(8, Math.min(inputRect.left, viewportWidth - width - 8))}px`,
    });
    listbox.style.top = openAbove
      ? `${Math.max(8, inputRect.top - listbox.offsetHeight - 4)}px`
      : `${inputRect.bottom + 4}px`;
  }

  function setActiveIndex(nextIndex, scroll = true) {
    activeIndex = visibleNames.length
      ? Math.min(Math.max(0, nextIndex), visibleNames.length - 1)
      : -1;
    const optionElements = listbox.querySelectorAll('[role="option"]');
    optionElements.forEach((option, index) => {
      const active = index === activeIndex;
      option.classList.toggle("is-active", active);
      option.setAttribute("aria-selected", active ? "true" : "false");
      if (active) {
        input.setAttribute("aria-activedescendant", option.id);
        if (scroll) option.scrollIntoView({ block: "nearest" });
      }
    });
    if (activeIndex < 0) input.removeAttribute("aria-activedescendant");
  }

  function commit(nextValue) {
    close(false);
    input.value = nextValue;
    onCommit(nextValue);
  }

  function renderOptions() {
    const query = dirty ? normalized(input.value) : "";
    visibleNames = fertilizerNames.filter((name) => !query || normalized(name).includes(query));
    if (!query) visibleNames.unshift("");
    if (!visibleNames.length) {
      listbox.classList.add("is-empty");
      listbox.textContent = noResultsLabel;
    } else {
      listbox.classList.remove("is-empty");
      const optionElements = visibleNames.map((name, index) => {
        const option = document.createElement("div");
        option.id = `${id}-option-${index}`;
        option.className = "searchable-combobox-option";
        option.dataset.index = String(index);
        option.textContent = name || emptyLabel;
        option.setAttribute("role", "option");
        return option;
      });
      listbox.replaceChildren(...optionElements);
    }
    const selectedIndex = dirty ? 0 : visibleNames.indexOf(selectedValue);
    setActiveIndex(Math.max(0, selectedIndex), false);
    positionListbox();
  }

  function handleGlobalEvent(event) {
    if (event.type !== "pointerdown") {
      positionListbox();
    } else if (!root.contains(event.target) && !listbox.contains(event.target)) {
      close();
    }
  }

  function openListbox() {
    if (listbox.isConnected) return;
    dirty = false;
    document.body.appendChild(listbox);
    input.setAttribute("aria-expanded", "true");
    document.addEventListener("pointerdown", handleGlobalEvent, true);
    document.addEventListener("scroll", handleGlobalEvent, true);
    window.addEventListener("resize", handleGlobalEvent);
    renderOptions();
  }

  function close(restore = true) {
    if (!listbox.isConnected) return;
    dirty = false;
    document.removeEventListener("pointerdown", handleGlobalEvent, true);
    document.removeEventListener("scroll", handleGlobalEvent, true);
    window.removeEventListener("resize", handleGlobalEvent);
    listbox.remove();
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    if (restore) input.value = selectedValue;
  }

  listbox.addEventListener("pointerdown", (event) => {
    const option = event.target.closest('[role="option"]');
    if (!option || !listbox.contains(option)) return;
    event.preventDefault();
    commit(visibleNames[Number(option.dataset.index)]);
  });

  input.addEventListener("focus", () => {
    openListbox();
    window.setTimeout(() => {
      if (document.activeElement === input) input.select();
    }, 0);
  });
  input.addEventListener("input", () => {
    if (!listbox.isConnected) openListbox();
    dirty = true;
    renderOptions();
  });
  input.addEventListener("keydown", (event) => {
    const direction = { ArrowDown: 1, ArrowUp: -1 }[event.key];
    if (direction) {
      event.preventDefault();
      if (!listbox.isConnected) openListbox();
      setActiveIndex(activeIndex < 0 ? 0 : activeIndex + direction);
      return;
    }
    if (event.key === "Enter" && listbox.isConnected && activeIndex >= 0) {
      event.preventDefault();
      commit(visibleNames[activeIndex]);
      return;
    }
    if (event.key === "Escape" && listbox.isConnected) {
      event.preventDefault();
      close();
    }
  });
  input.addEventListener("blur", () => window.setTimeout(close, 0));

  root.appendChild(input);
  return { element: root, destroy: () => close(false) };
}

export function createTable({ id, className, colgroupClasses, headerCells }) {
  const table = document.createElement("table");
  table.id = id;
  table.className = className;

  const colgroup = document.createElement("colgroup");
  colgroupClasses.forEach((colClass) => {
    const col = document.createElement("col");
    col.className = colClass;
    colgroup.appendChild(col);
  });
  table.appendChild(colgroup);

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headerCells.forEach((cell) => {
    const th = document.createElement("th");
    const label = cell.label;
    if (cell.onClick) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "table-sort-button";
      button.textContent = label;
      button.addEventListener("click", cell.onClick);
      th.classList.add("is-sortable");
      th.setAttribute("aria-sort", cell.sortDirection || "none");
      th.appendChild(button);
    } else {
      if (cell.labelKey) th.dataset.i18n = cell.labelKey;
      th.textContent = label;
    }
    if (cell.colSpan) {
      th.colSpan = cell.colSpan;
    }
    if (cell.title) {
      th.title = cell.title;
    }
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  table.appendChild(tbody);

  return { table, tbody };
}

export function renderTableRows(tableBody, rowCount, buildRow) {
  tableBody.innerHTML = "";
  for (let i = 0; i < rowCount; i += 1) {
    tableBody.appendChild(buildRow(i));
  }
}
