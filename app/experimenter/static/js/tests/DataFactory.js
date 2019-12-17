import faker from "faker";
import { AutoIncrementField, Factory, Field } from "experimenter/tests/factory";

export class VariantsFactory extends Factory {
  getFields() {
    return {
      id: new AutoIncrementField(),
      description: new Field(faker.lorem.sentence),
      name: new Field(faker.lorem.word),
      ratio: new Field(faker.random.number, { min: 1, max: 100 }),
      is_control: false,
    };
  }
}
export class AddonDataFactory extends Factory {
  getFields() {
    return {
      addon_release_url: new Field(faker.internet.url),
      variants: [],
      type: "addon",
    };
  }
  postGeneration() {
    super.postGeneration();
    const { generateVariants } = this.options;
    if (generateVariants) {
      const variants = [];
      for (let i = 0; i < generateVariants; i++) {
        variants.push(VariantsFactory.build());
      }
      this.data.variants = [...this.data.variants, ...variants];
    }
    if (this.data.variants.length) {
      this.data.variants[0].is_control = true;
    }
  }
}
