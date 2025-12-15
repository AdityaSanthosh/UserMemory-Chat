/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        orange: {
          primary: "#f97316", // Orange-500
          "primary-focus": "#ea580c", // Orange-600
          "primary-content": "#ffffff", // White text on primary

          secondary: "#fb923c", // Orange-400
          "secondary-focus": "#f97316", // Orange-500
          "secondary-content": "#ffffff", // White text on secondary

          accent: "#fed7aa", // Orange-200
          "accent-focus": "#fdba74", // Orange-300
          "accent-content": "#7c2d12", // Orange-900

          neutral: "#292524", // Stone-800
          "neutral-focus": "#1c1917", // Stone-900
          "neutral-content": "#fafaf9", // Stone-50

          "base-100": "#ffffff", // White
          "base-200": "#fff7ed", // Orange-50
          "base-300": "#ffedd5", // Orange-100
          "base-content": "#292524", // Stone-800

          info: "#3b82f6", // Blue-500
          "info-content": "#ffffff",

          success: "#22c55e", // Green-500
          "success-content": "#ffffff",

          warning: "#f59e0b", // Amber-500
          "warning-content": "#ffffff",

          error: "#ef4444", // Red-500
          "error-content": "#ffffff",
        },
      },
    ],
  },
};
