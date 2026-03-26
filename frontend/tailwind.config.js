/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                enterprise: {
                    bg: "#000000",
                    panel: "rgba(255, 255, 255, 0.02)",
                    surface: "rgba(255, 255, 255, 0.05)",
                    primary: "#FFFFFF",
                    "primary-hover": "#D1D5DB",
                    text: "#FFFFFF",
                    "text-muted": "#9CA3AF",
                    accent: "#3B82F6", // Minimal restrained blue accent
                    border: "rgba(255, 255, 255, 0.08)",
                    danger: "#EF4444",
                },
            },
            fontFamily: {
                sans: ["Inter", "Outfit", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "ui-monospace", "monospace"],
            },
            boxShadow: {
                glass: "0 8px 32px 0 rgba(0, 0, 0, 0.3)",
                neon: "0 0 15px rgba(255, 255, 255, 0.1)",
            },
            backdropBlur: {
                xs: "2px",
            },
            animation: {
                'pulse-ring': 'pulse-ring 3s cubic-bezier(0.215, 0.61, 0.355, 1) infinite',
            },
            keyframes: {
                'pulse-ring': {
                    '0%': { transform: 'scale(0.8)', opacity: '0.8' },
                    '100%': { transform: 'scale(2.5)', opacity: '0' },
                },
            },
        },
    },
    plugins: [],
};
