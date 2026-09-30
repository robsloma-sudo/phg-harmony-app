import { Agent, run } from "@openai/agents";

const harmony = new Agent({
  name: "Harmony",
  instructions: `
You are Harmony, the AI for Perfect Harmony Group.

For now, your only job is to prove that the OpenAI connection works.

Be concise, clear, and helpful.
`
});

export default async (req: Request) => {
  try {
    const body = await req.json();
    const message = body?.message;

    if (!message) {
      return Response.json(
        { error: "Missing message" },
        { status: 400 }
      );
    }

    const result = await run(harmony, message);

    return Response.json({
      answer: result.finalOutput
    });
  } catch (error) {
    return Response.json(
      {
        error: "Harmony failed",
        details: String(error)
      },
      { status: 500 }
    );
  }
};
