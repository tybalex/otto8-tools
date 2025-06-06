package commands

import (
	"context"
	"fmt"

	"github.com/obot-platform/tools/microsoft365/outlook/contact/pkg/client"
	"github.com/obot-platform/tools/microsoft365/outlook/contact/pkg/global"
	"github.com/obot-platform/tools/microsoft365/outlook/contact/pkg/graph"
	"github.com/obot-platform/tools/microsoft365/outlook/contact/pkg/util"
)

func CreateContact(ctx context.Context, givenName, surname, emails, businessPhones string) error {
	if givenName == "" && surname == "" && emails == "" && businessPhones == "" {
		fmt.Println("No parameters provided. Please provide at least one of the following parameters: given_name, surname, emails, business_phones")
		return nil
	}

	c, err := client.NewClient(global.AllScopes)
	if err != nil {
		return fmt.Errorf("failed to create client: %w", err)
	}

	emailAddresses := util.SplitString(emails)
	businessPhoneList := util.SplitString(businessPhones)
	contact, err := graph.CreateContact(ctx, c, givenName, surname, emailAddresses, businessPhoneList)
	if err != nil {
		return fmt.Errorf("failed to create contact: %w", err)
	}

	fmt.Printf("Contact created successfully. ID: %s\n", util.Deref(contact.GetId()))

	return nil
}
