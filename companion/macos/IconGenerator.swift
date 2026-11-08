import AppKit
import Foundation

guard CommandLine.arguments.count == 2 else {
    fputs("Usage: IconGenerator output.png\n", stderr)
    exit(64)
}

let side = 1024
let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: side,
    pixelsHigh: side,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
)!

NSGraphicsContext.saveGraphicsState()
let context = NSGraphicsContext(bitmapImageRep: bitmap)!
NSGraphicsContext.current = context
context.shouldAntialias = true
context.imageInterpolation = .high

NSColor(calibratedRed: 0.10, green: 0.16, blue: 0.34, alpha: 1).setFill()
NSBezierPath(roundedRect: NSRect(x: 24, y: 24, width: 976, height: 976), xRadius: 210, yRadius: 210).fill()

let indicatorColors: [NSColor] = [
    NSColor(calibratedRed: 0.35, green: 0.91, blue: 0.69, alpha: 1),
    NSColor(calibratedRed: 0.99, green: 0.77, blue: 0.31, alpha: 1),
    NSColor(calibratedRed: 0.42, green: 0.72, blue: 1.0, alpha: 1),
]
let rows: [CGFloat] = [696, 512, 328]
let widths: [CGFloat] = [432, 350, 390]
for index in rows.indices {
    indicatorColors[index].setFill()
    NSBezierPath(ovalIn: NSRect(x: 182, y: rows[index] - 23, width: 46, height: 46)).fill()
    NSColor(calibratedWhite: 0.94, alpha: 1).setFill()
    NSBezierPath(roundedRect: NSRect(x: 278, y: rows[index] - 15, width: widths[index], height: 30), xRadius: 15, yRadius: 15).fill()
}

let title = "C004" as NSString
title.draw(
    at: NSPoint(x: 212, y: 126),
    withAttributes: [
        .font: NSFont.systemFont(ofSize: 154, weight: .bold),
        .foregroundColor: NSColor(calibratedWhite: 1, alpha: 1),
        .kern: 4,
    ]
)

context.flushGraphics()
NSGraphicsContext.restoreGraphicsState()

let png = bitmap.representation(using: .png, properties: [:])!
try png.write(to: URL(fileURLWithPath: CommandLine.arguments[1]), options: .atomic)
