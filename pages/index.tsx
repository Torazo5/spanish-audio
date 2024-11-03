// nextjs-frontend/pages/index.tsx
import { Container, Typography, Box, TextField, Button } from "@mui/material";
import { useState } from "react";

export default function Home() {
  const [inputText, setInputText] = useState("");
  const [responseText, setResponseText] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const handleSubmit = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: inputText }),
      });

      const data = await response.json();
      if (response.ok) {
        setResponseText(data.text);
        // Append a timestamp to prevent caching
        setAudioUrl(`http://127.0.0.1:5000${data.audio_url}?t=${Date.now()}`);
      } else {
        setResponseText("An error occurred");
      }
    } catch (error) {
      setResponseText("An error occurred");
    }
  };

  const handlePlayAudio = () => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.play();
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <Typography variant="h4" align="center">
          Chat with GPT-4
        </Typography>
        <TextField
          label="Type your message..."
          variant="outlined"
          fullWidth
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
        <Button variant="contained" color="primary" onClick={handleSubmit}>
          Submit
        </Button>
        {responseText && (
          <Box mt={2} p={2} bgcolor="grey.800" borderRadius={4}>
            <Typography variant="body1" align="center" color="text.primary">
              {responseText}
            </Typography>
          </Box>
        )}
        {audioUrl && (
          <Button
            variant="contained"
            color="secondary"
            onClick={handlePlayAudio}
          >
            Play Audio
          </Button>
        )}
      </Box>
    </Container>
  );
}
