/** @type {import("tailwindcss").Config} */
export default {
  content: ["./src/**/*.{html,js,vue}", "./index.html"],
  theme: {
    extend: {},
  },
  screen: {
    sm: "480px",
    md: "768px",
    lg: "992px",
    xl: "1200px",
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["emerald", "dark"], // false: only light + dark | true: all themes | array: specific themes like this ["light", "dark", "cupcake"]
    darkTheme: "dark", // name of one of the included themes for dark mode
    base: false, // applies background color and foreground color for root element by default
    styled: true, // include daisyUI colors and design decisions for all components
    utils: true, // adds responsive and modifier utility classes
    prefix: "", // prefix for daisyUI classnames (components, modifiers and responsive class names. Not colors)
    logs: true, // Shows info about daisyUI version and used config in the console when building your CSS
  },
};
