import { boundClass } from "autobind-decorator";
import { fromJS, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Button, Container, Row, Col } from "react-bootstrap";

import AddonForm from "experimenter/components/AddonForm";
import GenericForm from "experimenter/components/GenericForm";
import PrefForm from "experimenter/components/PrefForm";
import { makeApiRequest } from "experimenter/utils/api";

@boundClass
class DesignForm extends React.PureComponent {
  static propTypes = {
    experimentType: PropTypes.string,
    slug: PropTypes.string,
  };

  constructor(props) {
    super(props);

    this.state = {
      data: new Map(),
      errors: new Map(),
      loaded: false,
      saving: false,
    };
  }

  getEndpointUrl() {
    return `experiments/${this.props.slug}/design-${this.props.experimentType}/`;
  }

  async componentDidMount() {
    const data = await makeApiRequest(this.getEndpointUrl());

    this.setState({
      loaded: true,
      data: fromJS(data),
    });
  }

  handleDataChange(key, value) {
    this.setState(({ data }) => ({
      data: data.set(key, value),
    }));
  }

  handleErrorsChange(key, value) {
    this.setState(({ errors }) => ({
      errors: errors.set(key, value),
    }));
  }

  async handleSubmit(event, redirectUrl) {
    event.preventDefault();

    this.setState({ saving: true });

    const requestSave = makeApiRequest(this.getEndpointUrl(), {
      method: "PUT",
      data: this.state.data.toJS(),
    });

    requestSave
      .then(() => {
        location.replace(redirectUrl);
      })
      .catch(err => {
        this.setState({
          errors: fromJS(err.data),
        });

        const invalid = document.querySelector(".is-invalid");
        if (invalid) {
          invalid.scrollIntoView();
        }
      })
      .finally(() => {
        this.setState({
          saving: false,
        });
      });
  }

  handleSubmitSave(event) {
    this.handleSubmit(event, `/experiments/${this.props.slug}/`);
  }

  handleSubmitContinue(event) {
    this.handleSubmit(
      event,
      `/experiments/${this.props.slug}/edit-objectives/`,
    );
  }

  render() {
    if (!this.state.loaded) {
      return (
        <Container>
          <div className="fa-5x">
            <Row className="justify-content-center">
              <i className="fas fa-spinner fa-spin" />
            </Row>
          </div>
        </Container>
      );
    }

    // Select the appropriate form component to use based on experiment type
    let Form;
    switch (this.state.data.get("type")) {
      case "pref":
        Form = PrefForm;
        break;
      case "multi-pref":
        Form = PrefForm;
        break;
      case "addon":
        Form = AddonForm;
        break;
      default:
        Form = GenericForm;
    }

    return (
      <div>
        <Container>
          <form onSubmit={this.handleSubmit} id="design-form">
            <Form
              handleDataChange={this.handleDataChange}
              handleErrorsChange={this.handleErrorsChange}
              data={this.state.data}
              errors={this.state.errors}
              loaded={this.state.loaded}
            />
            <Row>
              <Col className="text-right">
                <a
                  className="mr-1 btn btn-default"
                  href={`/experiments/${this.props.slug}/`}
                >
                  <span className="fas fa-times" /> Cancel Editing
                </a>

                <Button
                  disabled={this.state.saving}
                  variant="primary"
                  type="submit"
                  className="mr-1"
                  onClick={this.handleSubmitSave}
                >
                  <span className="fas fa-save" /> Save Draft
                </Button>

                <Button
                  disabled={this.state.saving}
                  id="save-continue"
                  variant="primary"
                  type="submit"
                  onClick={this.handleSubmitContinue}
                >
                  <span className="fas fa-save" /> Save Draft and Continue
                </Button>
              </Col>
            </Row>
          </form>
        </Container>
      </div>
    );
  }
}

export default DesignForm;
