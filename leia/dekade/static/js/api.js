import { Concept } from "./objects/concept.js";
import { Property } from "./objects/properties.js";
import { Sense } from "./objects/sense.js";


export async function contentIdToLEIAObject(contentId, contentType) {
    if (contentType == "lexicon.sense") {
        if (contentId[0] == "~") {
            contentId = contentId.slice(1);
        }

        return await apiKnowledgeLexiconSense(contentId);
    }

    if (contentType == "ontology.concept") {
        if (contentId[0] == "@") {
            contentId = contentId.slice(1);
        }

        return await apiKnowledgeOntologyConcept(contentId);
    }

    if (contentType == "properties.property") {
        if (contentId[0] == "$") {
            contentId = contentId.slice(1);
        }

        return await apiKnowledgePropertiesProperty(contentId);
    }

    console.error("Unknown contentId: " + contentId);
}


export async function apiKnowledgeLexiconFilter(filter) {
    try {
        const response = await axios.get("/api/knowledge/lexicon/filter/" + filter);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgeLexiconSense(sense, dataOnly = false) {
    try {
        const response = await axios.get("/api/knowledge/lexicon/sense/" + sense);

        if (dataOnly) {
            return response.data;
        }

        return new Sense(response.data);
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgeOntologyConcept(concept, dataOnly = false) {
    try {
        const response = await axios.get("/api/knowledge/ontology/concept/" + concept);

        if (dataOnly) {
            return response.data;
        }

        return new Concept(response.data);
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgeOntologyFilter(filter) {
    try {
        const response = await axios.get("/api/knowledge/ontology/filter/" + filter);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgeOntologyChildren(concept) {
    try {
        const response = await axios.get("/api/knowledge/ontology/children/" + concept);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgeOntologyWriteBlockFiller(concept, property, facet, filler, type) {
    try {
        const response = await axios.post("/api/knowledge/ontology/concept/" + concept + "/filler/block", {
            property: property,
            facet: facet,
            filler: filler,
            type: type
        });
        return response.data;
    } catch (error) {
        return error.data;
    }
}


export async function apiKnowledgePropertiesChildren(concept) {
    try {
        const response = await axios.get("/api/knowledge/properties/children/" + concept);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgePropertiesFilter(filter) {
    try {
        const response = await axios.get("/api/knowledge/properties/filter/" + filter);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgePropertiesProperty(property, dataOnly = false) {
    try {
        const response = await axios.get("/api/knowledge/properties/property/" + property);

        if (dataOnly) {
            return response.data;
        }

        return new Property(response.data);
    } catch (error) {
        console.error(error);
    }
}


export async function apiOntoSemAnalyze(input) {
    try {
        const response = await axios.post("/api/ontosem/analyze", {
            input: input
        });
        return response.data;
    } catch (error) {
        console.log(error);
        console.log(error.data);
        return error.data;
    }
}