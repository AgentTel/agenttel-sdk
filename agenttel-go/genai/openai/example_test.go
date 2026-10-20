package openai_test

import (
	"context"

	goopenai "github.com/sashabaranov/go-openai"

	agenttelopenai "go.agenttel.dev/agenttel-go/genai/openai"
)

// Wrap a go-openai client; every chat completion becomes a gen_ai.* span with
// token usage and agenttel.genai.cost_usd.
func ExampleWrap() {
	client := goopenai.NewClient("sk-...")
	traced := agenttelopenai.Wrap(client)

	_, _ = traced.CreateChatCompletion(context.Background(), goopenai.ChatCompletionRequest{
		Model:    goopenai.GPT4o,
		Messages: []goopenai.ChatCompletionMessage{{Role: goopenai.ChatMessageRoleUser, Content: "Hello"}},
	})
}
