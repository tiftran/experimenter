import { boundClass } from "autobind-decorator";
import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";

import DesignInput from "experimenter/components/DesignInput";
import PrefManager from "./PrefManager";

@boundClass
class MultiPrefBranchFields extends React.PureComponent {
    static propTypes = {
        branch: PropTypes.instanceOf(Map),
        errors: PropTypes.instanceOf(Map),
        handleChange: PropTypes.func,
        index: PropTypes.number,
    };

    handlePrefChange(value){
        this.props.handleChange("preferences",value)

    }

    renderField(name, label) {
        let helpContent;
        switch (name) {
            case "ratio":
                helpContent = (
                    <div>
                        <p>
                            Choose the size of this branch represented as a whole number. The
                            size of all branches together must be equal to 100. It does not
                            have to be exact, so these sizes are simply a recommendation of
                            the relative distribution of the branches.
                        </p>
                        <p>
                            <strong>Example:</strong> 50
                        </p>
                    </div>
                );
                break;

            case "name":
                helpContent = (
                    <div>
                        <p>
                            The control group should represent the users receiving the
                            existing, unchanged version of what you're testing. For example,
                            if you're testing making a button larger to see if users click on
                            it more often, the control group would receive the existing button
                            size. You should name your control branch based on the experience
                            or functionality that group of users will be receiving. Don't name
                            it 'Control Group', we already know it's the control group!
                        </p>
                        <p>
                            <strong>Example:</strong> Normal Button Size
                        </p>
                    </div>
                );
                break;

            case "description":
                helpContent = (
                    <div>
                        <p>
                            Describe the experience or functionality the control group will
                            receive in more detail.
                        </p>
                        <p>
                            <strong>Example:</strong> The control group will receive the
                            existing 80px sign in button located at the top right of the
                            screen.
                        </p>
                    </div>
                );
                break;

            case "value":
                helpContent = (
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
                );
                break;
        }

        return (
            <DesignInput
                label={label}
                name={`variants[${this.props.index}][${name}]`}
                id={`variants-${this.props.index}-${name}`}
                value={this.props.branch.get(name)}
                onChange={value => {
                    this.props.handleChange(name, value);
                }}
                error={this.props.errors.get(name)}
                helpContent={helpContent}
            />
        );
    }

    render() {
        return (
            <React.Fragment>
                {this.renderField("ratio", "Branch Size")}
                {this.renderField("name", "Name")}
                {this.renderField("description", "Description")}
                <PrefManager
                    preferences={this.props.branch.get("preferences")}
                    errors={this.props.errors.get("variants")}
                    variant_index={this.props.index}
                    onChange={value => {this.handlePrefChange(value);}}
                />
            </React.Fragment>
        );
    }
}

export default MultiPrefBranchFields;
