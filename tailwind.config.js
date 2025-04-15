/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/pages/**/*.{js,ts,jsx,tsx}",
    "./frontend/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mesa': {
          'blue': '#0058FF',
          'dark-blue': '#093C81',
          'black': '#131319',
          'gray': '#6F7186',
          'light-gray': '#E0E0E6',
          'white': '#FFFFFF',
          'gradient-start': '#0058FF',
          'gradient-end': '#4837EC',
        },
        'primary': {
          50: '#EEF4FF',
          100: '#D9E7FF',
          200: '#B5CFFF',
          300: '#80ACFF',
          400: '#4D88FF',
          500: '#0058FF', // MESA primary blue
          600: '#0046CC',
          700: '#003399',
          800: '#002266',
          900: '#001033',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Montserrat', 'sans-serif'],
      },
      boxShadow: {
        'mesa': '0 4px 20px rgba(0, 88, 255, 0.15)',
        'card': '0 2px 10px rgba(0, 0, 0, 0.05)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      backgroundImage: {
        'mesa-gradient': 'linear-gradient(90deg, #0058FF 0%, #4837EC 100%)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}; 