import { boundClass } from "autobind-decorator";
import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Button, Row, Col } from "react-bootstrap";
import DesignInput from "experimenter/components/DesignInput";
@boundClass
class Branch extends React.PureComponent {
    static propTypes = {
        preference: PropTypes.instanceOf(Map),
        errors: PropTypes.instanceOf(Map),
        index: PropTypes.number,
        onChange: PropTypes.func,
        remove: PropTypes.func,
    };

    handleChange(key, value) {
        const { onChange, preference } = this.props;
        onChange(preference.set(key, value));
    }

    renderTitle() {
        return <h4>Pref {this.props.index}</h4>;
    }

    renderRemoveButton() {
        const { index } = this.props;
        return (
            <Button
                variant="outline-danger"
                onClick={() => {
                    this.props.remove(index);
                }}
                id="remove-branch-button"
            >
                <span className="fas fa-times" /> Remove Pref
            </Button>
        );
    }

    renderInitialPrefInfoForm(){
            return (
                <div>
                    <DesignInput
                        label="Pref Name"
                        name="pref_key"
                        id="id_pref_key"
                        value={this.props.preference? this.props.preference.get("pref_name"): null}
                        error={"hi"}
                        helpContent={
                            <div>
                                <p>
                                    Enter the full name of the Firefox pref key that this experiment
                                    will control. A pref experiment can control exactly one pref,
                                    and each branch will receive a different value for that pref.
                                    You can find all Firefox prefs in about:config and any pref that
                                    appears there can be the target of an experiment.
                                </p>
                                <p>
                                    <strong>Example: </strong>
                                    browser.example.component.enable_large_sign_in_button
                                </p>
                            </div>
                        }
                    />

                    <DesignInput
                        label="Pref Type"
                        name="pref_type"
                        id="id_pref_type"
                        onChange={value => {
                            this.props.onChange("pref_type", value);
                        }}
                        value={this.props.preference? this.props.preference.get("pref_type"): null}
                        error={"klsjl"}
                        as="select"
                        helpContent={
                            <div>
                                <p>
                                    Select the type of the pref entered above. The pref type will be
                                    shown in the third column in about:config.
                                </p>
                                <p>
                                    <strong>Example:</strong> boolean
                                </p>
                            </div>
                        }
                    >
                        <option>Firefox Pref Type</option>
                        <option>boolean</option>
                        <option>integer</option>
                        <option>string</option>
                        <option>json string</option>
                    </DesignInput>

                    <DesignInput
                        label="Pref Branch"
                        name="pref_branch"
                        id="id_pref_branch"
                        onChange={value => {
                            this.props.onChange("pref_branch", value);
                        }}
                        value={this.props.preference? this.props.preference.get("pref_branch"): null}
                        error={"this"}
                        as="select"
                        helpContent={
                            <div>
                                <p>
                                    Select the pref branch the experiment will write its pref value
                                    to. If you're not sure what this means, you should stick to the
                                    'default' pref branch. Pref branches are a little more
                                    complicated than can be written here, but you can find&nbsp;
                                    <a href="https://developer.mozilla.org/en-US/docs/Archive/Add-ons/Code_snippets/Preferences#Default_preferences">
                                        more information here
                                    </a>
                                    .
                                </p>
                                <p>
                                    <strong>Example:</strong> default
                                </p>
                            </div>
                        }
                    >
                        <option>Firefox Pref Branch</option>
                        <option>default</option>
                        <option>user</option>
                    </DesignInput>
                    <DesignInput
                        label="Pref Value"
                        name="pref_value"
                        id="id_pref_value"
                        value={this.props.preference? this.props.preference.get("pref_value"): null}
                        error={"hi"}
                        helpContent={
                            <div>
                                <p className="mt-2">
                                    Choose the value of the pref for the control group. This value
                                    must be valid JSON in order to be sent to Shield. This should be
                                    the right type (boolean, string, number), and should be the value
                                    that represents the control or default state to compare to.
                                </p>
                                <p>
                                    <strong>Boolean Example:</strong> false
                                </p>
                                <p>
                                    <strong>String Example:</strong> some text
                                </p>
                                <p>
                                    <strong>Integer Example:</strong> 13
                                </p>
                            </div>
                        }
                    />
                </div>
            );
    }

    render() {

        return (
            <div key={this.props.index} id="control-branch-group">
                <Row className="mb-3">
                    <Col md={{ span: 4, offset: 3 }}>{this.renderTitle()}</Col>
                    <Col md={5} className="text-right">
                        {this.renderRemoveButton()}
                    </Col>
                </Row>
                {this.renderInitialPrefInfoForm()}

            </div>
        );
    }
}

export default Branch;
