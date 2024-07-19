

export async function apiKnowledgeOntologyFilter(filter) {
    try {
        const response = await axios.get("/api/knowledge/ontology/filter/" + filter);
        return response.data;
    } catch (error) {
        console.error(error);
    }
}