import click
import httpx
from lxml import etree

def _get_form_data(
    form_build_id: str,    email_address: str, name: str, surname: str
) -> dict[str, str]:
    return {
        "anon_mail[0][value]": email_address,
        "form_build_id": form_build_id,
        "form_id": "registration_basic_registration_register_form",
        "field_registration_name[0][value]": name,
        "field_registration_lname[0][value]": surname,
        "field_registration_enews[value]": "0",
        "op": "Register"
    }

@click.command()
@click.option(
    "--event-url",
    required=True,
    type=str,
)
@click.option(
    "--email-address",
    required=True,
    type=str,
)
@click.option(
    "--name",
    required=True,
    type=str,
)
@click.option(
    "--surname",
    required=True,
    type=str,
)
def main(
    event_url: str,
    email_address: str,
    name: str,
    surname: str,
):
    with httpx.Client() as client:
        get_response = client.get(url=event_url)

        get_response.raise_for_status()

        content = etree.HTML(get_response.content)
        
        message_text = content.xpath(
            './/div[@class="registration-message-styles"]/text()'
        )

        if message_text and (message := message_text.pop(0).lower()):
            if "coming soon" in message:
                raise RuntimeError("Registration is not yet open.")
            elif "closed" in message:
                raise RuntimeError("Registration is closed.")
            elif "capacity" in message:
                raise RuntimeError("Session is at capacity.")
        else:
            raise RuntimeError("Unable to get session's registration.")

        form_build_id_values = [i for i in content.xpath(".//input[@name='form_build_id']/@value")]

        if not form_build_id_values:
            raise RuntimeError(f"Could not find {form_build_id_values=} on the page.")

        form_build_id = form_build_id_values.pop(0)

        form_data = _get_form_data(
            form_build_id=form_build_id,
            email_address=email_address,
            name=name,
            surname=surname,
        )

        post_response = client.post(url=event_url, data=form_data, follow_redirects=True)

        post_response.raise_for_status()

        post_content = etree.HTML(post_response.content)

        confirmation_message = post_content.xpath(
            './/span[@class="field field--name-title field--type-string field--label-hidden"]/text()'
        )

        if confirmation_message and confirmation_message.pop(0).lower().startswith("thank"):
            return 
        else:
            raise RuntimeError("Failed to submit registration.")

if __name__ == "__main__":
    main()
