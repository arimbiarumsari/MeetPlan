# AI and Cloud Engineering

## Automatic meeting-time recommendation

The scheduler in `services/scheduler` provides an explainable baseline for
ranking meeting times. It applies the following rules:

- `busy` is a hard constraint and removes a candidate slot;
- `available` contributes `1.0` to the score;
- `tentative` contributes `0.5` to the score;
- a missing response is never assumed to be available;
- ties prefer fewer tentative participants and then the earliest slot.

Each recommendation includes the normalized score and the participant names
behind the explanation. This deterministic baseline can later be compared with
a learned ranking model after MeetPlan collects consented feedback data.

## Service interface

- `GET /health` returns a lightweight liveness response.
- `GET /ready` runs a deterministic scheduler self-check for container and
  orchestrator readiness probes.
- `POST /recommend` accepts participant availability and returns ranked slots.
- Invalid payloads return HTTP 400 with a JSON error. Payload validation covers
  structure, unique participant names, slot maps, and duplicate candidate
  slots. Successful responses include a model version and request-level counts.

Example request:

```json
{
  "participants": [
    {
      "name": "Bintang",
      "slots": {"2026-09-18T09:00": "available"}
    },
    {
      "name": "Arimbi",
      "slots": {"2026-09-18T09:00": "tentative"}
    }
  ]
}
```

## Cloud delivery baseline

The service uses only the Python standard library and is packaged in a
non-root Docker container listening on the platform-provided `PORT`. The
`Scheduler CI` workflow runs unit tests and builds the image for every relevant
change on branch `544012` and for pull requests. This prepares the service for
a managed container platform such as Cloud Run without committing credentials
or selecting a production cloud project prematurely.
