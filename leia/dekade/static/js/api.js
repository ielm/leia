import { Concept } from "./objects/concept.js";
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


export async function apiKnowledgeLexiconSense(sense) {
    try {
        const response = await axios.get("/api/knowledge/lexicon/sense/" + sense);
        return new Sense(response.data);
    } catch (error) {
        console.error(error);
    }
}


export async function apiKnowledgeOntologyConcept(concept) {
    try {
        const response = await axios.get("/api/knowledge/ontology/concept/" + concept);
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


export async function apiOntoSemAnalyze(input) {
    try {
        const response = await axios.post("/api/ontosem/analyze", {
            input: input
        });
        return response.data;
    } catch (error) {
        console.log(error);
    }
}