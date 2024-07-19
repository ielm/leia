import * as API from "../api.js";
import { LEIAObject } from "./_default.js";

export class Concept extends LEIAObject {

    constructor(content) {
        super();
        this.content = content;
    }

    prepareData() {
        return {
            ...super.prepareData(),
            name: this.name(),
            parents: this.parents(),
            definition: this.definition(),
            rows: this.rows(true).map(this._prepareRow),
        }
    }

    _prepareRow(row) {
        let prepared = {...row};
        prepared[row.row] = true;

        return prepared;
    }

    activateListeners(element) {
        element.find("button.concept-add-local").click(this._onAddLocalButtonClicked.bind(this));
        element.find("button.concept-del-local").click(this._onDelLocalButtonClicked.bind(this));
        element.find("button.concept-block-inherit").click(this._onBlockInheritButtonClicked.bind(this));
        element.find("button.concept-unblock-block").click(this._onUnblockBlockButtonClicked.bind(this));
        element.find("input.concept-toggle-inherited-display").change(this._onToggleInheritedDisplayChanged.bind(this));
    }

    templateName() {
        return "leia.knowledge.ontology.concept";
    }

    label() {
        return "@" + this.name();
    }

    name() {
        return this.content.name;
    }

    parents() {
        return this.content.parents;
    }

    definition() {
        return this.content.definition;
    }

    rows(sorted=true) {
        if (!sorted) {
            return this.content.rows;
        }

        // TODO: Improved sorting
        return this.content.rows.sort(function (a, b) {
            return a.property >= b.property;
        });
    }

    _onAddLocalButtonClicked(event) {
        console.log("TODO: add a local row to " + this.name());
    }

    _onDelLocalButtonClicked(event) {
        const concept = this.name();
        const property = $(event.currentTarget).data("property");
        const facet = $(event.currentTarget).data("facet");
        const filler = $(event.currentTarget).data("filler");

        console.log("TODO: remove " + property + "/" + facet + "/" + filler + " from " + concept);
    }

    async _onBlockInheritButtonClicked(event) {
        const concept = this.name();
        const from = $(event.currentTarget).data("from");
        const property = $(event.currentTarget).data("property");
        const facet = $(event.currentTarget).data("facet");
        const filler = $(event.currentTarget).data("filler");
        const type = $(event.currentTarget).data("type");

        console.log(await API.apiKnowledgeOntologyWriteBlockFiller(concept, property, facet, filler, type));
    }

    _onUnblockBlockButtonClicked(event) {
        const concept = this.name();
        const from = $(event.currentTarget).data("from");
        const property = $(event.currentTarget).data("property");
        const facet = $(event.currentTarget).data("facet");
        const filler = $(event.currentTarget).data("filler");

        console.log("TODO: unblock " + property + "/" + facet + "/" + filler + " in " + concept + " from " + from);
    }

    _onToggleInheritedDisplayChanged(event) {
        const show = $(event.currentTarget).is(':checked');
        const container = $(event.currentTarget).closest(".concept");

        if (show) {
            container.find("tr.concept-row-inherit").show();
        } else {
            container.find("tr.concept-row-inherit").hide();
        }
    }

}