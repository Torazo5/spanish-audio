import {
  Container,
  Typography,
  Box,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
} from "@mui/material";
import { useState } from "react";

export default function Home() {
  const [inputText, setInputText] = useState("");
  const [exerciseData, setExerciseData] = useState<any>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // State to store user's answers
  const [mcqAnswers, setMcqAnswers] = useState<string[]>([]);
  const [openEndedAnswers, setOpenEndedAnswers] = useState<string[]>([]);

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
        setExerciseData(data.data);
        setAudioUrl(`http://127.0.0.1:5000${data.audio_url}?t=${Date.now()}`);

        // Initialize answers arrays based on the number of questions
        setMcqAnswers(new Array(data.data.multiple_choice_questions.length).fill(''));
        setOpenEndedAnswers(new Array(data.data.open_ended_questions.length).fill(''));
      } else {
        setExerciseData(null);
      }
    } catch (error) {
      console.error("An error occurred:", error);
      setExerciseData(null);
    }
  };

  const handlePlayAudio = () => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.play();
    }
  };

  // Handler for MCQ answer selection
  const handleMcqAnswerChange = (questionIndex: number, selectedOption: string) => {
    const updatedAnswers = [...mcqAnswers];
    updatedAnswers[questionIndex] = selectedOption;
    setMcqAnswers(updatedAnswers);
  };

  // Handler for open-ended question answer input
  const handleOpenEndedAnswerChange = (questionIndex: number, value: string) => {
    const updatedAnswers = [...openEndedAnswers];
    updatedAnswers[questionIndex] = value;
    setOpenEndedAnswers(updatedAnswers);
  };

  // Function to submit answers to the backend (to be implemented)
  const handleSubmitAnswers = () => {
    // For now, just log the answers
    console.log('MCQ Answers:', mcqAnswers);
    console.log('Open-Ended Answers:', openEndedAnswers);
    // TODO: Send answers to backend via fetch POST request
  };

  return (
    <Container maxWidth="sm">
      <Box display="flex" flexDirection="column" alignItems="stretch" gap={2} mt={4}>
        <Typography variant="h4" align="center">
          Listening Practice Exercise
        </Typography>

        {/* Input field and Submit button */}
        <TextField
          label="Type your message..."
          variant="outlined"
          fullWidth
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
        <Button variant="contained" color="primary" onClick={handleSubmit}>
          Generate Exercise
        </Button>

        {/* Display the exercise data */}
        {exerciseData && (
          <Box mt={4}>
            {/* Display the listening text */}
            <Typography variant="h6">Text:</Typography>
            <Typography variant="body1" paragraph>
              {exerciseData.text}
            </Typography>

            {/* Play Audio Button */}
            {audioUrl && (
              <Button variant="contained" color="secondary" onClick={handlePlayAudio}>
                Play Audio
              </Button>
            )}

            {/* Display Multiple-Choice Questions */}
            {exerciseData.multiple_choice_questions && (
              <>
                <Typography variant="h6">Multiple-Choice Questions:</Typography>
                {exerciseData.multiple_choice_questions.map(
                  (mcq: any, index: number) => (
                    <Box key={index} mb={2}>
                      <Typography variant="subtitle1">
                        {index + 1}. {mcq.question}
                      </Typography>
                      <FormControl component="fieldset">
                        <RadioGroup
                          value={mcqAnswers[index] || ''}
                          onChange={(e) => handleMcqAnswerChange(index, e.target.value)}
                        >
                          {Object.entries(mcq.options).map(
                            ([optionKey, optionValue]: [string, any]) => (
                              <FormControlLabel
                                key={optionKey}
                                value={optionKey}
                                control={<Radio />}
                                label={`${optionKey}: ${optionValue}`}
                              />
                            )
                          )}
                        </RadioGroup>
                      </FormControl>
                    </Box>
                  )
                )}
              </>
            )}

            {/* Display Open-Ended Questions */}
            {exerciseData.open_ended_questions && (
              <>
                <Typography variant="h6">Open-Ended Questions:</Typography>
                {exerciseData.open_ended_questions.map(
                  (questionObj: any, index: number) => (
                    <Box key={index} mb={2}>
                      <Typography variant="subtitle1">
                        {index + 1}. {questionObj.question}
                      </Typography>
                      <TextField
                        variant="standard"
                        fullWidth
                        value={openEndedAnswers[index] || ''}
                        onChange={(e) => handleOpenEndedAnswerChange(index, e.target.value)}
                      />
                    </Box>
                  )
                )}
              </>
            )}

            {/* Button to submit answers */}
            <Button variant="contained" color="primary" onClick={handleSubmitAnswers}>
              Submit Answers
            </Button>
          </Box>
        )}
      </Box>
    </Container>
  );
}
