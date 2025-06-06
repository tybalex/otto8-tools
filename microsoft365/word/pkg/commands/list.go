package commands

import (
	"context"
	"fmt"

	"github.com/gptscript-ai/go-gptscript"
	"github.com/obot-platform/tools/microsoft365/word/pkg/client"
	"github.com/obot-platform/tools/microsoft365/word/pkg/global"
	"github.com/obot-platform/tools/microsoft365/word/pkg/graph"
)

func ListDocs(ctx context.Context) error {
	c, err := client.NewClient(global.ReadOnlyScopes)
	if err != nil {
		return err
	}

	infos, err := graph.ListDocs(ctx, c)
	if err != nil {
		return fmt.Errorf("failed to list word docs: %w", err)
	}

	if len(infos) == 0 {
		fmt.Println("No word docs found")
		return nil
	}

	gptscriptClient, err := gptscript.NewGPTScript()
	if err != nil {
		return fmt.Errorf("failed to create GPTScript client: %w", err)
	}

	var elements []gptscript.DatasetElement
	for _, info := range infos {
		elements = append(elements, gptscript.DatasetElement{
			DatasetElementMeta: gptscript.DatasetElementMeta{
				Name:        "doc_" + info.ID,
				Description: "User's personal word doc",
			},
			Contents: info.String(),
		})
	}

	datasetID, err := gptscriptClient.CreateDatasetWithElements(ctx, elements, gptscript.DatasetOptions{
		Name: "word_docs_list",
	})
	if err != nil {
		return fmt.Errorf("failed to create dataset: %w", err)
	}

	fmt.Printf("Created dataset with ID %s with %d docs\n", datasetID, len(elements))
	return nil
}
