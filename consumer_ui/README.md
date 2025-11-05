# SpendSense Consumer UI

Consumer-facing dashboard for SpendSense financial education platform.

## Features

- **Education Page**: Personalized financial education content with rationale boxes
- **Insights Page**: Financial behavior signals and analytics
- **Transactions Page**: Transaction history and spending overview
- **Offers Page**: Partner offers and recommendations

## Tech Stack

- React 19 + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui components
- React Router

## Development

```bash
cd consumer_ui
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

For production, set `VITE_API_URL` to your deployed API URL.

## Building for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Deployment to Vercel

1. Connect your repository to Vercel
2. Set the root directory to `consumer_ui`
3. Set framework preset to "Vite"
4. Add environment variable `VITE_API_URL` pointing to your API
5. Deploy

## User ID

For demo purposes, the app uses `user_001` as the default user ID. In production, this should come from authentication.
