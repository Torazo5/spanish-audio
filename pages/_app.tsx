// pages/_app.tsx
import type { AppProps } from "next/app";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";

// Create a dark theme
const darkTheme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#0a0a0a", // Background color for the entire app
      paper: "#171717", // Background color for paper-based components
    },
    text: {
      primary: "#ededed", // Primary text color for dark mode
    },
  },
});

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline /> {/* Normalizes CSS and applies global background */}
      <Component {...pageProps} />
    </ThemeProvider>
  );
}

export default MyApp;
