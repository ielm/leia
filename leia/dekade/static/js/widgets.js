

export class ContextMenu {

    constructor() {
        this.rendered = undefined;
        this.options = [];

        this.template = Handlebars.compile(`
            <div class="context-menu">
                <ul>
                    {{#each options}}
                    <li class="context-menu-option" data-option-index="{{@key}}">{{this.label}}</li>
                    {{/each}}
                </ul>
            </div>
        `);
    }

    addOption(label, callback) {
        this.options.push({label: label, callback: callback});
    }

    show(x, y) {
        $("body").find(".context-menu").hide();

        const menu = this.template({options: this.options});

        this.rendered = $(menu);
        this.rendered.find(".context-menu-option").on("click", this._callback.bind(this));
        this.rendered.css({"left": x + "px", "top": y + "px"});

        $("body").append(this.rendered);
        $("body").on("click.contextmenu", this.hide.bind(this));
    }

    hide() {
        this.rendered.remove();

        $("body").off("click.contextmenu");
    }

    _callback(event) {
        const option = $(event.currentTarget);
        const index = parseInt(option.data("option-index"));
        const callback = this.options[index].callback;
        callback();
    }

}