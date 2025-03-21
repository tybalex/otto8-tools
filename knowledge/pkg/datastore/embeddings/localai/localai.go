package localai

import (
	"fmt"
	"strings"

	"dario.cat/mergo"
	"github.com/gptscript-ai/knowledge/pkg/datastore/embeddings/load"
	cg "github.com/philippgille/chromem-go"
)

type EmbeddingProviderLocalAI struct {
	Model string `koanf:"model" env:"LOCALAI_MODEL" export:"required"`
}

func (p *EmbeddingProviderLocalAI) UseEmbeddingModel(model string) {
	p.Model = model
}

const EmbeddingProviderLocalAIName = "localai"

func (p *EmbeddingProviderLocalAI) EmbeddingModelName() string {
	return p.Model
}

func (p *EmbeddingProviderLocalAI) Name() string {
	return EmbeddingProviderLocalAIName
}

func (p *EmbeddingProviderLocalAI) Configure() error {
	if err := load.FillConfigEnv(strings.ToUpper(EmbeddingProviderLocalAIName), &p); err != nil {
		return fmt.Errorf("failed to fill LocalAI config from environment: %w", err)
	}

	if err := p.fillDefaults(); err != nil {
		return fmt.Errorf("failed to fill LocalAI defaults: %w", err)
	}

	return nil
}

func (p *EmbeddingProviderLocalAI) fillDefaults() error {
	defaultCfg := EmbeddingProviderLocalAI{
		Model: "bert-cpp-minilm-v6",
	}

	if err := mergo.Merge(p, defaultCfg); err != nil {
		return fmt.Errorf("failed to merge LocalAI config: %w", err)
	}

	return nil
}

func (p *EmbeddingProviderLocalAI) EmbeddingFunc() (cg.EmbeddingFunc, error) {
	return cg.NewEmbeddingFuncLocalAI(p.Model), nil
}

func (p *EmbeddingProviderLocalAI) Config() any {
	return p
}
