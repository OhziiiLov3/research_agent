import axios from "axios";

export async function askAgent(query, history) {
  const response = await axios.post("http://localhost:8000/api/research", {
    query,
    history,
  });
  return response.data;
}