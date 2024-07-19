import { Concept } from "./objects/concept.js";


export async function contentIdToLEIAObject(contentId) {
    if (contentId[0] == "@") {
        return await apiKnowledgeOntologyConcept(contentId.slice(1));
    }

    console.error("Unknown contentId: " + contentId);
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