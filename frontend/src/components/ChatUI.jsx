// frontend/src/components/ChatUI.jsx
import { useState } from "react";
import { askAgent } from "../api/agentApi";
import { Box, TextField, Button, Paper, Typography } from "@mui/material";

export default function ChatUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages([...messages, userMessage]);

    try {
      const res = await askAgent(input, messages);
      const agentMessage = { role: "agent", content: res.answer };
      setMessages((prev) => [...prev, agentMessage]);
      setInput("");
    } catch (err) {
      const errorMsg = { role: "agent", content: "Something went wrong!" };
      setMessages((prev) => [...prev, errorMsg]);
      console.error(err);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      height="100vh"
      p={2}
      bgcolor="#f5f5f5"
    >
      <Box flex={1} overflow="auto" mb={2}>
        {messages.map((m, i) => (
          <Paper
            key={i}
            sx={{
              p: 1,
              my: 1,
              maxWidth: "60%",
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              bgcolor: m.role === "user" ? "primary.light" : "grey.300",
            }}
          >
            <Typography>{m.content}</Typography>
          </Paper>
        ))}
      </Box>

      <Box display="flex" gap={1}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Ask me something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <Button variant="contained" onClick={sendMessage}>
          Send
        </Button>
      </Box>
    </Box>
  );
}
