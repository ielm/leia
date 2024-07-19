import * as Widgets from "./widgets.js";


class LEIATabsViewer {

    constructor(tabPanel, contentPanel) {
        this.tabPrototype = TabButton;
        this.tabPanel = $(tabPanel);
        this.contentPanel = $(contentPanel);
        this.index = {};
    }

    _addTab(name, label) {
        const tab = new this.tabPrototype(this, name, label);
        this.tabPanel.append(tab);

        return tab;
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

}


class LEIAFixedTabsViewer extends LEIATabsViewer {

    constructor(tabPanel, contentPanel) {
        super(tabPanel, contentPanel);

        for (var content of this.contentPanel.children(".fixed-tab-content")) {
            content = $(content);

            const name = content.data("tab-name");
            const label = content.data("tab-label");
            const tab = this._addTab(name, label);

            this.index[name] = {
                name: name,
                tab: tab,
                contents: content
            };
        }

        this.select($(this.contentPanel.children(".fixed-tab-content").first()).data("tab-name"));
    }

}


class LEIAObjectTabsViewer extends LEIATabsViewer {

    constructor(tabPanel, contentPanel) {
        super(tabPanel, contentPanel);
        this.tabPrototype = ObjectTabButton;
    }

    async addObject(leiaObject, select=true) {
        // leiaObject must be a LEIAObject type

        const name = leiaObject.name();
        if (name in this.index) {
            // Select the tab if it already exists.
            this.select(name);
            return;
        }

        const tab = this._addTab(leiaObject.name(), leiaObject.label());
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

    async _addContents(leiaObject) {
        const contents = await leiaObject.html();
        contents.addClass("tab-contents-hidden");
        this.contentPanel.append(contents);

        return contents;
    }

}

class TabButton extends HTMLButtonElement {

    constructor(tabs, name, label) {
        super();

        this.tabs = tabs;

        this.name = name;
        this.setAttribute("is", "tab-button");
        this.setAttribute("data-tab-name", name);
        this.innerHTML = label;
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

        this.tabs.select(this.name);
    }

}


class ObjectTabButton extends TabButton {

    constructor(tabs, name, label) {
        super(tabs, name, label);
        this.oncontextmenu = this._onRightClicked;
    }

    _onRightClicked(event) {
        event.preventDefault();
        const menu = new Widgets.ContextMenu();
        menu.addOption("Pin", this.pin);
        menu.addOption("Close", this.close);

        menu.show(event.pageX, event.pageY);
    }

    pin() {
        console.log("TODO: PIN");
    }

    close() {
        console.log("TODO: CLOSE");
    }

}


customElements.define("tab-button", TabButton, { extends: "button" });
customElements.define("object-tab-button", ObjectTabButton, { extends: "button" });

export const sidebarTabs = new LEIAFixedTabsViewer("#leia-sidebar-tabs", "#leia-sidebar-content");
export const contentTabs = new LEIAObjectTabsViewer("#leia-tabs-navigator", "#leia-tabs-content");