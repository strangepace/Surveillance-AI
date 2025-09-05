# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/abc4f80a-3ba6-4a90-9e46-cade4450f23f

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/abc4f80a-3ba6-4a90-9e46-cade4450f23f) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/abc4f80a-3ba6-4a90-9e46-cade4450f23f) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)

---

## Live Mode (Real‑time Alerts)

This project includes a live alerts experience powered by a WebSocket client and REST fallbacks.

- Pages: `/live` (simple), `/live-alerts` (full feed & bulk actions)
- WebSocket: built in `src/lib/liveClient.ts` using `API_BASE` to resolve `wss://` URL
- REST helpers: see `src/lib/api.ts` (ack, pin, note, export)
- Auto‑fallback: after repeated connection instability, the app switches to mock mode

How to use:
1) Run the app: `npm run dev`
2) Open `/live-alerts`
3) Use the Dev Panel (bottom‑right) to toggle "Use real API" on/off
4) Pick a Camera ID (via URL or UI) to connect; history loads via REST

Backend expectations:
- WebSocket endpoint: `/ws/live?cameraId=...` (returns JSON messages with `{ type: "alert", data }`)
- REST endpoints used are implemented via `api.ts` helpers

## Developer Tools
- Dev Panel: simulate categories, toggle jitter FPS, clear alerts, force live burst, switch real vs mock
- Dev Banner: shows connection state (mock/unstable) and developer mock setting

## Releases
- Phase‑1 Complete (planned v0.1.0): live WebSocket integration, automatic mock fallback, DevBanner, optimistic updates (ack/pin/note), export clip flow in LiveReview, URL‑synced filters, and assorted fixes.

See CHANGELOG.md for details.

---

## Setup & Run

Requirements:
- Node.js LTS (v18+ recommended) and npm

Install and start:
```sh
npm install
cp .env.example .env.local   # then set values
npm run dev
```

## Environment Variables
Create `.env.local` with the following keys (see `.env.example`):
- `API_BASE_URL=` HTTP API base (e.g., https://api.example.com)
- `WS_BASE_URL=` WebSocket origin (e.g., wss://api.example.com) — optional; derived from API if omitted
- `NEXT_PUBLIC_ENABLE_MOCKS=false` Force mock mode for live
- `NEXT_PUBLIC_DEFAULT_CAMERA_ID=` Optional default camera id

Notes:
- The app resolves base URLs via `src/lib/api.ts` and WebSocket join helpers in `src/lib/ws.ts`.
- A developer-only `/verify` page is available in development to test health and WS.
- Use the in-app Dev Panel (bottom-right) on live pages to toggle real vs mock.

## Scripts
- `npm run dev` — start the dev server
- `npm run build` — production build
- `npm run preview` — preview the production build locally
- `npm run lint` — run ESLint
