import logging
from typing import Type
import ollama

import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)

api_key = CONSTANTS['ASSEMBLYAI_API_KEY']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def on_begin(self: Type[StreamingClient], event: BeginEvent):
    print(f"Session started: {event.id}")


def on_turn(self: Type[StreamingClient], event: TurnEvent):
    print(f"{event.transcript} ({event.end_of_turn})")
    print(f"{event.end_of_turn_confidence}")

    if event.end_of_turn and not event.turn_is_formatted:
        params = StreamingSessionParameters(
            format_turns=True,
        )

        self.set_params(params)
    
    if event.end_of_turn:
        print("Turn ended - terminating session")
        print(event.transcript)
        move = get_ai_response(event.transcript)
        if move:
            print(f"AI Move: {move}")
        else:
            print("No valid move detected.")


def get_ai_response(transcript: str) -> str:
    ollama_stream = ollama.chat(
        model="deepseek-r1:7b",
        messages=[{"role": "user", "content": "You are a chess interpretor, given a users fen string , colour and an audio transcript about the move they'd like to make you are to return the move they are trying to make in uci format. If the user is not trying to make a move, return an empty string." + transcript}],
        stream=True,
    )

    response_text = ""
    for chunk in ollama_stream:
        response_text += chunk['message']['content']
    
    return response_text.strip()

def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    print(
        f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
    )


def on_error(self: Type[StreamingClient], error: StreamingError):
    print(f"Error occurred: {error}")


def main():
    client = StreamingClient(
        StreamingClientOptions(
            api_key=api_key,
            api_host="streaming.assemblyai.com",
        )
    )

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    client.connect(
        StreamingParameters(
            sample_rate=16000,
            format_turns=True,
        )
    )

    try:
        client.stream(
          aai.extras.MicrophoneStream(sample_rate=16000)
        )
    finally:
        client.disconnect(terminate=True)


if __name__ == "__main__":
    main()
