import { boundClass } from "autobind-decorator";
import { fromJS, List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, Button, Card } from "react-bootstrap";

import Pref from "experimenter/components/Pref";

@boundClass
class PrefManager extends React.PureComponent {
    static propTypes = {
        preferences: PropTypes.instanceOf(List),
        errors: PropTypes.instanceOf(List),
        onChange: PropTypes.func
    };

    handleChange(index, value){
        const{
            preferences,
            onChange,
        } = this.props;

        onChange(preferences.set(index, value))
    }


    addPref() {
        const {
            preferences,
            errors,
            onChange,
            handleErrorsChange,
        } = this.props;
        onChange(preferences.push(fromJS({})));
    }

    removePref(index) {
        const {
            preferences,
            errors,
            onChange,
            handleErrorsChange,
        } = this.props;
        let pref = preferences.toJS();
        const spliced_preference = fromJS(pref);

        onChange(spliced_preference);
        //handleErrorsChange("preferences", errors.delete(index));
    }

    renderPref(preference, index) {
        const {  errors } = this.props;

        return (
           <Pref
               key={index}
               index={index}
               preference={preference}
               remove={this.removePref}
               onChange={(value)=>this.handleChange(index, value)}
           />
        );
    }

    render() {
        const { preferences } = this.props;

            return (
                <React.Fragment>
                    {preferences.map((p, i) => this.renderPref(p, i))}
                    <Row>
                        <Col className="text-right">
                            <Button
                                id="add-pref-button"
                                variant="outline-success"
                                className="mb-4"
                                onClick={this.addPref}
                            >
                                <span className="fas fa-plus" /> Add Pref
                            </Button>
                        </Col>
                    </Row>
                </React.Fragment>
            );
    }
}
export default PrefManager;
