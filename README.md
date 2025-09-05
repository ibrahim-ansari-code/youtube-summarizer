# youtube summarizer

basically takes youtube videos and makes summaries using AI agents. has a web interface and can publish to google docs if you want.

## what it does

- web ui with real-time updates
- works with multiple languages (auto-detects best transcript)
- gets video title and channel info
- cleans up transcript text
- ai review of summaries
- optional google docs publishing
- websocket progress updates

## setup

install stuff:
```bash
pip install -r requirements.txt
```

add your openai key to `.env`:
```
OPENAI_API_KEY=your_key_here
```

for google docs (optional):
- make google cloud project + enable docs api
- download credentials.json
- put it in project root

## how it works

1. extract - gets transcript + metadata
2. clean - removes timestamps and filler
3. summarize - ai makes summary
4. review - quality check
5. publish - uploads to gdocs (optional)

## tech stack

flask + socketio, crewai, openai api, google apis, bootstrap
