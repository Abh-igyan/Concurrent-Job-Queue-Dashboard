/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "#10151f",
        panel2: "#151b26",
        border: "#263142",
        accent: "#4fd1c5",
        warn: "#fbbf24",
        danger: "#fb7185",
        ok: "#34d399"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Consolas"]
      }
    }
  },
  plugins: []
};
