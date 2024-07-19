

class LEIATabsViewer {

    constructor() {
        this.tabPanel = $("#leia-tabs-navigator");
        this.contentPanel = $("#leia-tabs-content");

        this.index = {};
    }

    async addObject(leiaObject, select=true) {
        // leiaObject must be a LEIAObject type

        const name = leiaObject.name();
        if (name in this.index) {
            // Select the tab if it already exists.
            this.select(name);
            return;
        }

        const tab = this._addTab(leiaObject);
        const contents = await this._addContents(leiaObject);

        this.index[name] = {
            name: name,
            tab: tab,
            contents: contents
        };

        if (select) {
            this.select(name);
        }
    }

    select(name) {
        // Unselect all tabs, and hide all current content
        for (var _tab of Object.values(this.index)) {
            _tab.tab.setSelected(false);
            _tab.contents.addClass("tab-contents-hidden");
        }

        // Select the desired tab
        const tab = this.index[name];
        tab.tab.setSelected(true);

        // Show the current content
        tab.contents.removeClass("tab-contents-hidden");
    }

    _addTab(leiaObject) {
        const tab = new TabButton(leiaObject);
        this.tabPanel.append(tab);

        return tab;
    }

    async _addContents(leiaObject) {
        const contents = await leiaObject.html();
        contents.addClass("tab-contents-hidden");
        this.contentPanel.append(contents);

        return contents;
    }

}

class TabButton extends HTMLButtonElement {

    constructor(leiaObject) {
        super();

        this.name = leiaObject.name();
        this.setAttribute("is", "tab-button");
        this.setAttribute("data-tab-name", leiaObject.name());
        this.innerHTML = leiaObject.label();
        this.selected = false;

        this.addEventListener("click", e => { this._onClicked(e) });
    }

    setSelected(selected) {
        this.selected = selected;

        if (selected) {
            this.classList.add("selected");
        } else {
            this.classList.remove("selected");
        }
    }

    _onClicked(event) {
        if (this.selected) { return; }

        tabs.select(this.name);
    }

}

customElements.define("tab-button", TabButton, { extends: "button" });

export const tabs = new LEIATabsViewer();