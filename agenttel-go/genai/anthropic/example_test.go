package anthropic_test

import (
	"context"

	"github.com/anthropics/anthropic-sdk-go"

	agenttelanthropic "go.agenttel.dev/agenttel-go/genai/anthropic"
)

// Wrap the Anthropic Messages service; every message call becomes a gen_ai.*
// span with token usage and agenttel.genai.cost_usd.
func ExampleWrap() {
	client := anthropic.NewClient()
	traced := agenttelanthropic.Wrap(&client.Messages)

	_, _ = traced.CreateMessage(context.Background(), anthropic.MessageNewParams{
		Model:     anthropic.ModelClaudeSonnet4_5,
		MaxTokens: 1024,
		Messages:  []anthropic.MessageParam{anthropic.NewUserMessage(anthropic.NewTextBlock("Hello"))},
	})
}
