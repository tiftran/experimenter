import React from "react";
import {
  render,
  cleanup,
  waitForDomChange,
  fireEvent,
} from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import DesignForm from "experimenter/components/DesignForm";
import * as Api from "experimenter/utils/api";
import { waitForFormToLoad } from "experimenter/tests/helpers.js";
import { AddonRolloutFactory } from "./DataFactory";

describe("The `DesignForm` component for Addons", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const mockSuccessResponse = AddonRolloutFactory.build();
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));

    return mockSuccessResponse;
  };

  const rejectedSetUp = () => {
    const mockSuccessResponse = AddonRolloutFactory.build();
    const rejectResponse = {
      data: { addon_release_url: ["This field is required."] },
    };
    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(mockSuccessResponse)
      .mockRejectedValueOnce(rejectResponse);
  };

  it("renders addonRollout forms", async () => {
    setup();
    const { getAllByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalled();

    expect(getAllByText("Description")).toHaveLength(1);
    expect(getAllByText("Signed Add-On URL")).toHaveLength(1);
  });

  it("click on addon radio button switches to addon forms", async () => {
    const mockSuccessResponse = AddonRolloutFactory.build();
    mockSuccessResponse.rollout_type = "pref";
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));
    const designForm = await render(<DesignForm experimentType={"rollout"} />);
    const { getByText, getByLabelText, container } = designForm;

    await waitForFormToLoad(container);

    expect(Api.makeApiRequest).toHaveBeenCalled();
    expect(getByText("Pref Value")).toBeInTheDocument();
    expect(getByText("Pref Name")).toBeInTheDocument();
    expect(getByText("Pref Type")).toBeInTheDocument();

    fireEvent.click(getByLabelText("Add-On Rollout"));

    expect(getByText("Signed Add-On URL")).toBeInTheDocument();
  });

  it("Saves and Redirects", async () => {
    delete location.replace;
    location.replace = jest.fn();
    setup();
    const { getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );
    await waitForFormToLoad(container);
    fireEvent.click(getByText("Save Draft and Continue"));
    expect(getByText("Save Draft and Continue")).toHaveAttribute("disabled");

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    let button = getByText("Save Draft and Continue");
    // wait for button to no longer be disabled
    await waitForDomChange({ button });
    expect(location.replace).toHaveBeenCalled();
  });

  it("Cancels and nothing is saved ", async () => {
    setup();
    const { getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);

    fireEvent.click(getByText("Cancel Editing"));

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);
  });

  it("Make Edits to Form and is saved ", async () => {
    const data = setup();
    const { getByTestId, getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const designValue = " it's my design description value";
    const addonUrlValue = "https://example.com";
    const designInput = getByTestId("design");
    const addonUrlInput = getByTestId("addonUrl");
    fireEvent.change(designInput, { target: { value: designValue } });
    fireEvent.change(addonUrlInput, { target: { value: addonUrlValue } });

    expect(designInput.value).toBe(designValue);
    expect(addonUrlInput.value).toBe(addonUrlValue);

    fireEvent.submit(getByText("Save Draft and Continue"));

    data.design = designValue;
    data.addon_release_url = addonUrlValue;
    expect(Api.makeApiRequest).toBeCalledWith(expect.anything(), {
      data: data,
      method: "PUT",
    });
  });

  it("Make addon url blank, returns a required field error", async () => {
    rejectedSetUp();
    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByTestId, getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const designInput = getByTestId("design");
    const addonUrlInput = getByTestId("addonUrl");

    const designValue = " it's my design description value";

    fireEvent.change(designInput, { target: { value: designValue } });
    fireEvent.change(addonUrlInput, { target: { value: "" } });

    fireEvent.submit(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(addonUrlInput);

    expect(getByText("This field is required.")).toBeInTheDocument();
  });
});
