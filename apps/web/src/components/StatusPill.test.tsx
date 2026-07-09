import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { StatusPill } from "./StatusPill";

test("renders the label uppercase-styled per Linen conventions", () => {
  render(<StatusPill label="Platform scaffold" />);
  const pill = screen.getByText("Platform scaffold");
  expect(pill.className).toContain("uppercase");
  expect(pill.className).toContain("rounded-full");
});
